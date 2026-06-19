from abc import ABC, abstractmethod
from typing import Dict, List

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
    def __init__(self, subject: str, policyId: str) -> None:
        self.subject = subject
        self.policyId = policyId

    @abstractmethod
    async def get_telemetry(self) -> List[DittoProtocolEnvelope]:
        raise NotImplementedError()

    def create_topic(
        self,
        thingName: str,
        channel: Channel = Channel.TWIN,
        criterion: Criterion = Criterion.COMMAND,
        action: Action | None = CommandAction.MODIFY,
    ) -> Topic:
        return Topic(
            subject=self.subject,
            channel=Channel.TWIN,
            thingName=thingName,
            group=Group.THING,
            criterion=Criterion.COMMAND,
            action=CommandAction.MODIFY,
        )

    def create_envelope(
        self,
        message_topic: Topic,
        attributes: dict[str, object] | None = None,
        features: Dict[str, Feature] | None = None,
    ) -> DittoProtocolEnvelope:
        thing = Thing(
            policyId=self.policyId,
            features=features,
            attributes=attributes,
        )

        env = DittoProtocolEnvelope(topic=message_topic, value=thing)
        return env
