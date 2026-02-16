from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


from interfaces.hono import HonoDevice
from models.ditto import (
    Channel,
    CommandAction,
    Criterion,
    DittoProtocolEnvelope,
    Feature,
    Group,
    Thing,
    Topic,
)


class Device(ABC):
    def __init__(self, hono_dev: HonoDevice):
        self._hono = hono_dev
        self.id = hono_dev.id

    def modify_message(
        self,
        thingName: str,
        attributes: "Optional[dict[str, object]]" = None,
        features: Optional[Dict[str, Feature]] = None,
    ) -> DittoProtocolEnvelope:
        message_topic = Topic(
            namespace=self._hono.id,
            channel=Channel.TWIN,
            thingName=thingName,
            group=Group.THING,
            criterion=Criterion.COMMAND,
            action=CommandAction.MODIFY,
        )

        thing = Thing(
            thingId=thingName,
            policyId=self._hono.policyId,
            features=features,
            attributes=attributes,
        )

        env = DittoProtocolEnvelope(topic=message_topic, value=thing)
        return env

    @abstractmethod
    async def modify(self, device: Any, data: Any) -> None:
        pass
