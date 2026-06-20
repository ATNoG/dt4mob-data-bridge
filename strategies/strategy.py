from abc import ABC, abstractmethod
from typing import Any, Dict, List

from models.ditto import (
    Action,
    Channel,
    CommandAction,
    Criterion,
    DittoProtocolEnvelope,
    Feature,
    Group,
    Thing,
    Topic,
)


class BaseStrategy(ABC):
    def __init__(self, namespace: str, subject: str, policyId: str) -> None:
        self.namespace = namespace
        self.subject = subject
        self.policyId = policyId

    @abstractmethod
    async def get_telemetry(self) -> List[DittoProtocolEnvelope]:
        raise NotImplementedError()

    def _create_topic(
        self,
        thingName: str,
        channel: Channel = Channel.TWIN,
        criterion: Criterion = Criterion.COMMAND,
        action: Action | None = CommandAction.MODIFY,
    ) -> Topic:
        return Topic(
            namespace=self.namespace,
            channel=Channel.TWIN,
            thingName=f"{self.subject}:{thingName}",
            group=Group.THING,
            criterion=Criterion.COMMAND,
            action=CommandAction.MODIFY,
        )

    def _create_envelope(
        self,
        topic: Topic,
        attributes: dict[str, object] | None = None,
        features: Dict[str, Feature] | None = None,
        path: str = "/",
    ) -> DittoProtocolEnvelope:
        thing = Thing(
            thingId=f"{topic.namespace}:{topic.thingName}",
            policyId=self.policyId,
            features=features,
            attributes=attributes,
        )

        return DittoProtocolEnvelope(topic=topic, path=path, value=thing)

    def _create_envelope_raw(
        self,
        message_topic: Topic,
        value: Any = None,
        path: str = "/",
    ) -> DittoProtocolEnvelope:
        return DittoProtocolEnvelope(topic=message_topic, path=path, value=value)
