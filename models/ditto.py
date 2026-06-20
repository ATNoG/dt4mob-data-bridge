from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Self, Union

from pydantic import BaseModel, ConfigDict, Field, model_serializer, model_validator
from typing_extensions import Annotated

RequestedAck = Annotated[str, Field(pattern=r"[a-zA-Z0-9-_:]{3,100}")]


class Group(str, Enum):
    THING = "things"
    POLICY = "policies"
    CONNECTION = "connections"


class Channel(str, Enum):
    TWIN = "twin"
    LIVE = "live"


class Criterion(str, Enum):
    COMMAND = "commands"
    EVENT = "events"
    SEARCH = "search"
    MESSAGE = "messages"
    ERROR = "errors"
    ACK = "acks"
    ANNOUNCEMENT = "announcements"


class CommandAction(str, Enum):
    CREATE = "create"
    RETRIEVE = "retrieve"
    MODIFY = "modify"
    MERGE = "merge"
    DELETE = "delete"


class EventAction(str, Enum):
    CREATED = "created"
    MODIFIED = "modified"
    MERGED = "merged"
    DELETED = "deleted"


MessageAction = Annotated[
    str, Field(pattern=r"^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")
]

AcknowledgementAction = Annotated[str, Field(pattern=r"[a-zA-Z0-9-_:]{3,100}")]

AnnouncementAction = str


class SearchAction(str, Enum):
    SUBSCRIBE = "subscribe"
    REQUEST = "request"
    CANCEL = "cancel"
    CREATED = "created"
    NEXT = "next"
    COMPLETE = "complete"
    FAILED = "failed"


Action = Union[
    CommandAction,
    EventAction,
    MessageAction,
    AcknowledgementAction,
    SearchAction,
    AnnouncementAction,
]


class Topic(BaseModel):
    namespace: str
    thingName: str
    group: Group
    channel: Optional[Channel]
    criterion: Criterion
    action: Optional[Action]

    @model_validator(mode="after")
    def check_criterion_action(self) -> Self:
        match self.criterion:
            case Criterion.COMMAND:
                if not isinstance(self.action, CommandAction):
                    raise ValueError("Action invalid for this criterion")

            case Criterion.EVENT:
                if not isinstance(self.action, EventAction):
                    raise ValueError("Action invalid for this criterion")

            case Criterion.SEARCH:
                if not isinstance(self.action, SearchAction):
                    raise ValueError("Action invalid for this criterion")

            case Criterion.ANNOUNCEMENT:
                if not isinstance(self.action, AnnouncementAction):
                    raise ValueError("Action invalid for this criterion")

        return self

    @model_serializer
    def ser_model(self) -> str:
        if self.channel:
            res = f"{self.namespace}/{self.thingName}/{self.group.value}/{self.channel.value}/{self.criterion.value}"
        else:
            res = f"{self.namespace}/{self.thingName}/{self.group.value}/{self.criterion.value}"

        if self.action:
            action_value = (
                self.action.value if isinstance(self.action, Enum) else str(self.action)
            )
            res += f"/{action_value}"

        return res


class Headers(BaseModel):
    model_config = ConfigDict(validate_by_name=True)

    content_type: Annotated[Optional[str], Field(alias="content-type")] = None
    correlation_id: Annotated[str, Field(alias="correlation-id")]
    ditto_originator: Annotated[Optional[str], Field(alias="ditto-originator")] = None
    if_Match: Annotated[Optional[str], Field(alias="If-Match")] = None
    if_None_Match: Annotated[Optional[str], Field(alias="If-None-Match")] = None
    if_equal: Annotated[Optional[str], Field(alias="if-equal")] = None
    response_required: Annotated[Optional[bool], Field(alias="response-required")] = (
        None
    )
    requested_acks: Annotated[
        Optional[List[RequestedAck]], Field(alias="requested-acks")
    ] = None
    timeout: Annotated[Optional[str], Field()] = None
    version: Annotated[Optional[int], Field(ge=1, le=2)] = None
    condition: Annotated[Optional[str], Field()] = None


class Feature(BaseModel):
    definition: Optional[str] = None
    properties: Dict[str, Any] = {}
    desiredProperties: Optional[Dict[str, Any]] = None


class Thing(BaseModel):
    thingId: str
    policyId: str
    definition: Optional[str] = None
    attributes: Optional[Dict[str, Any]] = None
    features: Optional[Dict[str, Feature]] = None


# TODO: Policy and connection models

DittoEnvelopeValue = Union[Thing]


class DittoProtocolEnvelope(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    topic: Topic
    headers: Optional[Headers] = None
    path: str = "/"
    fields: Optional[str] = None
    value: Optional[DittoEnvelopeValue] = None
    extra: Optional[Dict[str, Any]] = None

    # Events
    revision: Optional[float] = None
    timestamp: Optional[datetime] = None


DittoMessage = Iterable[DittoProtocolEnvelope]
