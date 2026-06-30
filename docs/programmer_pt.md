# Execução do programa e lógica principal

O programa principal, conforme implementado atualmente, comportar-se-á da seguinte forma:

![Diagrama de Fluxo de Controlo do Data Bridge](/Users/iavcoelho/IT/DT4MOB/data-bridge/docs/figs/ctrl_flow_diagram.png)

As principais adições podem ser feitas implementando mais strategies, que podem
modificar o comportamento de um determinado dispositivo. Estas strategies são responsáveis por criar
Mensagens de Envelope do Protocolo Ditto, que o Device enviará para o Eclipse Hono, que
as reencaminhará para o Eclipse Ditto. Este protocolo pode ser consultado na [documentação
oficial do Eclipse
Ditto](https://eclipse.dev/ditto/protocol-overview.html), e o Modelo de
Dados para o encapsulamento deste comando está definido em `models/ditto.py`.

Adicionalmente, o diagrama de sequência do fluxo de execução principal é o seguinte:

![Diagrama de sequência do Data Bridge](/Users/iavcoelho/IT/DT4MOB/data-bridge/docs/figs/seq_diagram_main.png)

# Estrutura do Código

O programa está estruturado logicamente da seguinte forma:

![Diagrama de dependências e estrutura de código do Data Bridge](/Users/iavcoelho/IT/DT4MOB/data-bridge/docs/figs/dependency_diagram.png)

> **_NOTA_**: Para facilitar a compreensão deste diagrama: É utilizada uma notação `ball and
> socket`, onde uma bola representa o fornecimento de uma interface, e uma socket
> representa o consumo dessa interface. É usado para mostrar as dependências
> entre componentes internos do sistema (e a interação com sistemas
> externos). A coluna `App Core` consiste nos ficheiros `main.py`,
> `devices/device.py` e nos contidos em `utils.py`. A
> coluna `Strategies` consiste nos ficheiros dentro do diretório `strategies`
> e a coluna `Interfaces` consiste nos ficheiros contidos no diretório
> `interfaces`. Para facilitar a compreensão, as dependências da
> camada de dados foram removidas, mas esses ficheiros estão contidos nos diretórios `models`
> e `storage`.

Em `main.py`, são criadas várias instâncias de `Device`, para cada um dos
dispositivos configurados. Esta classe pode ser observada em `devices/device.py`.

Este `Device` contém um mecanismo de batching que aguardará 2 segundos entre
o envio de 100 mensagens, para garantir que a instância do Eclipse Hono não fique
sobrecarregada com demasiadas mensagens. Este mecanismo de batching é importado de `utils/batch.py`.

# Modelos de Dados

Os modelos de dados neste projeto são todos criados usando o `BaseModel` do `Pydantic`,
com Enums a serem criados com a classe `Enum` da biblioteca padrão do Python.

Para saber mais sobre como criar um modelo `Pydantic`, recomenda-se a consulta da
sua [documentação
oficial](https://pydantic.dev/docs/validation/2.11/get-started/).
No entanto, os conceitos importantes são que uma nova classe tem de ser criada
que estenda a classe `BaseModel`, e os campos são definidos dentro desta nova classe,
juntamente com os seus tipos. O `Pydantic` é então responsável pela serialização
e desserialização do modelo. Validadores personalizados podem ser criados com o
decorador de função `@model_validator`.

Por uma questão de organização, espera-se que estes modelos sejam criados
dentro de um novo ficheiro no diretório `models/`, com um nome que permita
o fácil reconhecimento da finalidade dos modelos.

# Singletons

Para efeitos de caching, ou para ter uma instância comum que precise de ser
partilhada entre diferentes classes no projeto, como é o caso da partilha de um
`ClientSession` entre as diferentes interfaces, são usados Singletons. São
classes que contêm internamente uma única instância de uma determinada classe e têm
métodos que permitem o acesso a essa classe. No caso do `SessionSingleton`
presente em `storage/session.py`, a instância medeia o acesso a uma única
instância de `ClientSession` através do método `get_session()` definido da seguinte forma:

```python
@classmethod
def get_session(cls) -> ClientSession:
    if cls.client is None:
        cls.client = ClientSession()

    return cls.client
```

O singleton é responsável por criar a instância única no caso de
esta não existir, bem como por fechar e eliminar essa instância quando já não for
necessária, através do método `close_session()`:

```python
@classmethod
async def close_session(cls) -> None:
    if cls.client:
        await cls.client.close()
        cls.client = None
```

Adicionalmente, se necessário, o singleton pode também adicionar lógica antes de aceder ao
recurso partilhado, como acionar um mutex ou um lock para garantir que não haja
condições de corrida em acesso paralelo, como é o caso do `StationSingleton`:

```python
@classmethod
async def set_stations(cls, stations: List[Station]) -> None:
    async with cls._lock:
        cls._stations = set(stations)
```

Existem atualmente dois singletons implementados, no diretório `storage/`,
sendo eles o `SessionSingleton` já mencionado e o `StationSingleton`.

Com o `SessionSingleton` já descrito anteriormente, o `StationSingleton`
medeia o acesso a um conjunto partilhado de objetos `Station` e a um dicionário que
associa o ID de uma área de aviso ao objeto `WarningArea`. Permite depois que outros
componentes definam os itens no conjunto ou no dicionário, bem como obter um
item do dicionário, obter um determinado objeto `WarningArea` pelo seu ID e
também obter as estações mais próximas de um determinado ponto, dado um raio.

# Interfaces

O conceito de `interface` neste programa não é o de uma interface padrão
que define as funções obrigatórias que precisam de ser implementadas. É apenas
a definição do contacto com o mundo exterior e está, para o bem ou para o
mal, fortemente acoplada à `strategy` que a utiliza. Como tal, a
definição desta interface é deixada completamente ao critério da pessoa programadora. No entanto,
algumas recomendações são deixadas, nomeadamente a utilização da classe `SessionSingleton`
para adquirir um `ClientSession` do `aiohttp` no caso de ser usada uma API REST
como fonte de dados. Espera-se que a interface retorne um Modelo personalizado
que tenha sido definido na secção anterior, e que as funções
definidas nesta interface sejam apenas chamadas nas respetivas strategies.

Adicionalmente, foi seguida a diretriz de que todas as funções utilitárias definidas dentro do ficheiro
devem ser prefixadas com um underscore (`_`), bem como as funções
principais na strategy serem prefixadas com `get`, como em
`get_meteorologic_data`, ou `get_meteorologic_warnings`, por exemplo.

Por uma questão de organização, espera-se que estas classes sejam criadas
dentro de um novo ficheiro no diretório `interfaces/`, com um nome que permita
o fácil reconhecimento da finalidade dessa interface.

## Interface Hono

A interface Hono é responsável por manter um `ClientSession` com a
instância Eclipse Hono fornecida e enviar mensagens para o seu Adaptador HTTP. As
mensagens são enviadas para o endpoint `/telemetry` do Adaptador HTTP como um pedido
POST, com o conteúdo da mensagem a ser enviado no corpo desse pedido como
um objeto JSON.

Adicionalmente, esta interface é também responsável por carregar o contexto
SSL/TLS do dispositivo configurado, bem como o certificado x509 do Eclipse Hono no
caso de este ser fornecido através da configuração.

Antes de fazer o pedido, a interface calcula o tamanho total da
mensagem a ser enviada e, no caso de ser maior que 4k bytes, a
mensagem não é enviada, pois seria maior do que o Hono aceita. No caso
de o pedido retornar qualquer código de erro, a interface regista o erro, mas não
tenta enviar o pedido novamente.

## Interface HonoMock

A interface HonoMock é uma interface de depuração que, em vez de enviar o
pedido HTTP para o Eclipse Hono, simplesmente regista o objeto JSON que seria enviado.

## Interface IPMA

A interface IPMA é responsável por interagir com a API aberta da IPMA,
adquirindo as estações, as suas medições, os avisos que a IPMA fornece e
as áreas que estes afetam. Adicionalmente, também fornece funções para preencher o
`StationSingleton` com as estações meteorológicas e áreas de aviso adquiridas.

Ao adquirir os avisos meteorológicos, a interface filtra para manter apenas
aqueles cujo aviso é "yellow" ou "red", descartando os que são
classificados como "gray" ou "green".

## Interface Waze

A interface Waze é responsável por interagir com a API Connected
Citizens do Waze, adquirindo os Jams e Alerts registados na plataforma do Waze.

A API CCP do Waze aceita uma bounding box, e não um ponto central e raio como
o Data Bridge está configurado. Como tal, a interface, dado o centro e o raio
configurados, calculará os limites de uma área retangular que circunscreve
a área definida. Isto é feito convertendo o raio de pesquisa na sua
distância equivalente em graus decimais, que é depois adicionada e subtraída
às coordenadas do ponto central. Estas coordenadas recém-calculadas definem
4 linhas, cuja interseção define a bounding box que é enviada para a API.

# Devices

A classe `Device`, definida em `devices/device.py`, contém o ciclo de vida de um
dispositivo. A classe fornece um método assíncrono `run` que iterará
através das strategies configuradas no dispositivo e executará o seu
método `get_telemetry()`. Depois, para cada `DittoProtocolEnvelope` retornado, o
método `send_telemetry()` da interface `HonoDevice` é chamado para enviar a mensagem para
o Eclipse Hono. Após executar todo o ciclo de vida, a classe `Device`
fecha automaticamente o `ClientSession` instanciado para esse dispositivo.

# Strategies

Este Data Bridge foi construído com o conceito de facilidade de extensibilidade em mente,
e tenta tornar o mais simples possível a criação de novos módulos responsáveis
por adquirir dados de diferentes fontes, tais como outras APIs relevantes que possam
precisar de ser utilizadas para adicionar mais informação à representação
do mundo Digital Twin.

Para tal, é utilizado o conceito de `Strategies`, que recebe o nome do
[Strategy Pattern](https://refactoring.guru/design-patterns/strategy), onde uma
família de algoritmos é definida mas intercambiável entre si.

O processo de criação de uma nova fonte de dados passa pela criação de uma nova
extensão da classe `BaseStrategy`. Adicionalmente, é também de notar o
conceito de `interface`, que neste projeto é considerado o ato de
interagir com serviços externos, e de `model` que é onde os
dados recuperados são armazenados. Como exemplo, temos a interface `ipma` (definida em `interfaces/ipma.py`), que é
responsável por todas as interações feitas com a [API
IPMA](https://api.ipma.pt), e os modelos `meteo` (definidos em
`models/meteo.py`) que contêm todos os dados relevantes para esta
interação, nomeadamente a estação meteorológica, medição e modelação
de dados de aviso meteorológico, juntamente com os Enums e constantes necessários.

Outro exemplo é a interface `geojson`, responsável por interagir com
ficheiros GeoJSON no sistema de ficheiros.

Para criar uma nova fonte de dados, espera-se que primeiro os modelos de dados sejam
definidos, seguindo-se as interações com o mundo exterior e, por último, a
definição da própria classe strategy.

Devido à intercambialidade destas classes, todas elas estendem a mesma classe
base e têm a mesma "interface" no sentido standard de programação, onde
cada subclasse deve implementar a função assíncrona `get_telemetry(self) -> List[DittoProtocolEnvelope]`.

A definição desta classe `BaseStrategy` pode ser vista no ficheiro
[strategies/strategy.py](../strategies/strategy.py). A classe deve
obrigatoriamente conter os seguintes campos:

- `namespace`
- `subject`
- `policyId`

Que devem ser definidos no construtor da classe (função `__init__`).
Adicionalmente, a classe base contém as seguintes funções utilitárias:

```python
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

Que auxiliam na criação do DittoProtocolEnvelope.

Por último, aquando da criação da nova classe `Strategy`, o ficheiro
[strategies/__init__.py](../strategies/__init__.py) deve ser alterado para permitir
a configuração desta nova strategy a partir do ficheiro de configuração `config.toml`.

Para tal, deve ser criada uma nova classe prefixada com underscore que defina
os campos necessários para a strategy. Adicionalmente, esta classe DEVE estender a
classe `_BaseType` definida nesse ficheiro e DEVE ser adicionada à união de tipos
`StrategyType`. É obrigatório que esta classe recém-criada contenha o campo
`type`, que deve ser definido como uma string literal.

Como exemplo da criação de tal classe, temos a classe `_GeoJSON`, que
permite a definição da `GeoJsonStrategy` no ficheiro de configuração:

```python

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

Por último, a instanciação da strategy DEVE ser adicionada à função
`_type_to_strategy()`, também definida no mesmo ficheiro. Para tal, uma nova
entrada no `match`, correspondendo ao tipo da classe, tem de ser
adicionada, que retorna a instanciação do objeto.

Como exemplo:
```python
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

Dado tudo isto, a configuração da strategy no ficheiro de configuração é
automaticamente tratada pelo data bridge, não sendo necessárias mais alterações.

De seguida, é especificada a implementação concreta de todas as strategies.

## Strategy Meteorológica

A strategy meteorológica é responsável por consultar a API aberta da IPMA e
recuperar as medições obtidas das suas estações meteorológicas.

O fluxo de execução desta strategy é o seguinte:

![Diagrama de sequência da Strategy Meteo](/Users/iavcoelho/IT/DT4MOB/data-bridge/docs/figs/seq_meteo_strat.png)

Conforme definido pela `BaseStrategy`, esta classe tem um método `get_telemetry` que,
quando chamado, fará um pedido `GET` à API aberta da IPMA e recuperará um
ficheiro GeoJSON que contém não apenas as medições de todas as estações
online, mas também alguns atributos sobre essas estações, nomeadamente a localização e a
cidade onde estão localizadas.

A partir destes dados adquiridos, as estações são filtradas de modo a que apenas
as estações com medições recentes (aquelas recolhidas há menos de 2 horas) sejam mantidas.
Adicionalmente, o `StationsSingleton`, que atua como cache para as localizações
das Estações, é atualizado.

Depois, para cada estação contida no ficheiro GeoJSON recuperado, uma
instância de `DittoProtocolEnvelope` é criada e adicionada a um array, que será
depois retornado ao ciclo de execução principal para que uma instância de `Device` envie para
o Eclipse Hono.

Como é comum noutros Digital Twins criados, os campos `geotile` e `expiry_ts`
são adicionados ao Thing, auxiliando na procura de Things numa determinada área
geográfica, bem como permitindo que o sistema de coleta de lixo elimine things
não utilizados e desatualizados.

## Strategy de Avisos Meteorológicos

A strategy meteorológica é responsável por consultar a API aberta da IPMA e
recuperar os avisos que foram atribuídos a cada região do país.

O fluxo de execução desta strategy é o seguinte:

![Diagrama de sequência da Strategy Warnings](/Users/iavcoelho/IT/DT4MOB/data-bridge/docs/figs/seq_warnings_strat.png)

Atualmente, esta strategy assume que o StationSingleton já foi
preenchido com as estações meteorológicas e áreas de aviso existentes, o que
está a ser feito no início do programa. A partir daqui, para cada
aviso ativo, a área de aviso é recuperada do singleton, e a sua
localização é usada para calcular as 3 estações mais próximas, e os avisos são
agrupados por estas estações.

Depois, para cada estação, um comando `modify` `DittoProtocolEnvelope` é
instanciado e adicionado a um array, que é depois retornado para o fluxo
de execução principal para que uma instância de `Device` envie para o Eclipse Hono.

Como é comum noutros Digital Twins criados, os campos `geotile` e `expiry_ts`
são adicionados ao Thing, auxiliando na procura de Things numa determinada área
geográfica, bem como permitindo que o sistema de coleta de lixo elimine things
não utilizados e desatualizados.

## Strategy de Trânsito

A strategy de trânsito é responsável por consultar a API Connected Citizens
Program do Waze e recuperar os `alerts` e `jams` atuais registados no Waze.

O fluxo de execução desta strategy é o seguinte:

![Diagrama de sequência da Strategy Traffic](/Users/iavcoelho/IT/DT4MOB/data-bridge/docs/figs/seq_traffic_strat.png)

Após adquirir os dados da interface, procede primeiro à criação de um
`DittoProtocolEnvelope` para criar ou modificar um Thing, seguido da criação
de uma mensagem para modificar a feature `alerts` nesse Thing e, por último, percorrendo
todos os jams e criando uma mensagem separada para modificar a
feature `jams`.
Isto é feito desta forma porque, no caso dos `jams`, devido ao campo
de geometria do jam, a mensagem pode tornar-se bastante grande e exceder
o limite de tamanho do Eclipse Hono. Fazer uma mensagem separada por jam garante que
a mensagem não excede o limite e, se exceder, apenas um único Jam é perdido,
e não a atualização completa do Thing.

Todos os envelopes produzidos são adicionados a um array, que é depois retornado ao
fluxo de execução principal para que uma instância de `Device` envie para o Eclipse Hono.

Como é comum noutros Digital Twins criados, os campos `geotile` e `expiry_ts`
são adicionados ao Thing, auxiliando na procura de Things numa determinada área
geográfica, bem como permitindo que o sistema de coleta de lixo elimine things
não utilizados e desatualizados.

## Strategy GeoJSON

Esta strategy difere das restantes porque a fonte de dados utilizada vem
do sistema de ficheiros local em vez de ser obtida através de um pedido HTTP.
A esta strategy é fornecido um ficheiro ou diretório, e esta lerá o(s)
ficheiro(s) e, a partir daí, extrairá as features contidas no ficheiro.

O fluxo de execução desta strategy é o seguinte:

![Diagrama de sequência da Strategy GeoJSON](/Users/iavcoelho/IT/DT4MOB/data-bridge/docs/figs/seq_geojson_strat.png)

O campo `name` do GeoJSON é usado para nomear os Things que devem ser
criados/atualizados. A partir do array `features`, os campos `properties` e `geometry`
são usados para preencher os atributos do Thing.

Esta strategy foi criada com a intenção de lidar com ficheiros GeoJSON cujas
coordenadas estão na projeção `ETRS89`, significando que também converte essas
coordenadas para `WGS84`, pois essa é a projeção que está atualmente a ser usada
pelo sistema.

Como é comum noutros Digital Twins criados, os campos `geotile` e `expiry_ts`
são adicionados ao Thing, auxiliando na procura de Things numa determinada área
geográfica, bem como permitindo que o sistema de coleta de lixo elimine things
não utilizados e desatualizados.
