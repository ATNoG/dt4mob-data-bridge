# Extension of the Data Bridge

This Data Bridge was built with the concept of ease of extensibility in mind,
and attempts to make it as simple as possible to create new modules responsible
for acquiring data from different sources, such as other relevant APIs that may
need to be used to add more information to the Digital Twin world
representation.

To do so, the concept of `Strategies` are used, getting their name from the
[Strategy Pattern](https://refactoring.guru/design-patterns/strategy), where a
family of algorithms is defined but interchangeable between them.

The process of creating a new data source revolves around creating a new
extension of the  `BaseStrategy` class. In addition, it is also of note the
concept of an `interface`, which in this project is considered the act of
interacting with external serivces, and of a `model` which is where the
retrieved data is stored. As an example, we have the `ipma` interface (defined in `interfaces/ipma.py`), which is
responsible for all the interactions being made with the [IPMA
API](https://api.ipma.pt), and the `meteo` models (defined in
`models/meteo.py`) which contain all of the data that is relevant to this
interaction, namely the meteorologic station, measurement and meteorologic
warning data modelling, along with the needed Enums and constants.

Another example is the `geojson` interface, responsible for interacting with
GeoJSON files in the file system.

To create a new data source, it is expected that first the data models are
defined, following by the interactions with the outside world and lastly the
definition of the strategy class itself.

## Data Models

The data models in this project are all created using `Pydantic`'s `BaseModel`,
with Enums being created with Python's stdlib `Enum` class.

To see more about how to create a `Pydantic` model, please consult their
[official
documentation](https://pydantic.dev/docs/validation/2.11/get-started/)

However, the important concepts are that a new class has to be created that
extends the `BaseModel` class, and fields are defined within this new class,
along with their types. `Pydantic` is then responsible for the serialization
and deserialization of the model. Custom validators can be created with the
`@model_validator` function decorator. Once again, consultation of the
[official
documentation](https://pydantic.dev/docs/validation/2.11/get-started/) is
highly recommended.

For a matter of organization, it is expected that these models are created
within a new file in the `models/` directory, with a name that allows for the
ease of recognition on what the purpose of these models is.

## Interface

The concept of a `interface` in this program is not one of a standard interface
that defines the mandatory functions that need to be implemented. It is just
the definition of the contact with the outside world and is, for better or for
worse, tightly coupled with the `strategy` that uses it. As such, the
definition of this interface is left completely to the programmer. However,
some recommendations are left, namely the usage of the `SessionSingleton` class
to acquire a `aiohttp`'s `ClientSession` in the case that a REST API is used
for the data source. It is expected that the interface returns a custom Model
that has been defined in the previous section, and that the functions defined
in this interface are only called on the respective strategies.

Additionally, the guideline that all utility functions defined within the file
should be prefixed with a underscore (`_`) was followed, as well as the main
functions in the strategy being prefixed with `get`, as in
`get_meteorologic_data`, or `get_meteorologic_warnings`, for example.

For a matter of organization, it is expected that these classes are created
within a new file in the `interfaces/` directory, with a name that allows for the
ease of recognition on what the purpose of such an interface is.

## Strategy

Due to the interchangeability of these classes, they all extend the same base
class and have the same "interface" in the standard programming sense, where
each subclsas must implement the asynchronous `get_telemetry(self) -> List[DittoProtocolEnvelope]` 
function.

The definition of this `BaseStrategy` class can be seen in the
[strategies/strategy.py](../strategies/strategy.py) file. The class must
mandatorily contain the following fields:

- `namespace`
- `subject`
- `policyId`

Which are to be set in the class's constructor (`__init__` function).
Additionaly, the base class contains the following utility functions:

```py
    def _create_topic(
        self,
        thingName: str,
        channel: Channel = Channel.TWIN,
        criterion: Criterion = Criterion.COMMAND,
        action: Action | None = CommandAction.MODIFY,
    ) -> Topic:


    def _create_envelope(
        self,
        topic: Topic,
        attributes: dict[str, object] | None = None,
        features: Dict[str, Feature] | None = None,
        path: str = "/",
    ) -> DittoProtocolEnvelope:


    def _create_envelope_raw(
        self,
        message_topic: Topic,
        value: Any = None,
        path: str = "/",
    ) -> DittoProtocolEnvelope:
```

which aid in the creation of the DittoProtocolEnvelope.

Lastly, upon creation of the new `Strategy` class, the file
[strategies/__init__.py](../strategies/__init__.py) should be altered to allow
for the configuration of this new strategy from the `config.toml` config file.

To do so, a new class prefixed with underscore shall be created that defines
the fields required by the strategy. In addition, this class MUST extend the
`_BaseType` class defined in that file and MUST be added to the `StrategyType`
type union. It is mandatory that this newly created class contains the field
`type`, which is to be set as a string literal.

As an example of the creation of such class is the `_GeoJSON` class, which
allows for the definition of the `GeoJsonStrategy` in the configuration file:

```py

class _GeoJson(_BaseType):
    type: Literal["geojson"] = "geojson"
    dir: str | None = None
    file: str | None = None

    @model_validator(mode="after")
    def validate_fields(self) -> Self:
        if (self.dir is None) == (self.file is None):
            raise ValueError(
                "A GeoJson strategy must either have files or directories, not both"
            )
        return self

StrategyType = Annotated[
    Union[_Meteo, _Traffic, _GeoJson, _MeteoWarnings], Field(discriminator="type")
]
```


Lastly, the instantiation of the strategy MUST be added to the
`_type_to_strategy()` function, also defined in the same file. To do so, a new
entry in the `match` statement, matching against the class type has to be
added, which returns the instantiation of the object.

As an example:
```py
def _type_to_strategy(
    type: StrategyType,
    policyId: str,
    namespace: str,
) -> BaseStrategy:
    match type:
        (...)
        case _GeoJson():
            return GeoJsonStrategy(
                namespace, type.subject, policyId, type.dir, type.file
            )
```

Given all this, the configuration of the strategy in the configuration file is
automatically handled by the data bridge, and no more changes need to be made.
