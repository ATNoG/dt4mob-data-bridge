# Data Bridge

O Data Bridge é um serviço de integração de dados que consulta
várias fontes de dados rodoviários e meteorológicos (IPMA, Waze e ficheiros GeoJSON
locais) e encaminha os dados normalizados para um registo de dispositivos IoT Eclipse Hono
utilizando o protocolo Eclipse Ditto sobre HTTP.

## Pré-requisitos

Antes de utilizar o Data Bridge, certifique-se de que tem:

| Requisito | Versão/Detalhes |
| ----------- | --------------- |
| Python      | 3.13 ou superior  |
| Eclipse Hono | Instância com um adaptador HTTP configurado usando autenticação baseada em certificado |
| Ambiente virtual Python | Um ambiente virtual configurado, quer usando `uv` ou qualquer outro sistema compatível com PEP-518 |
| Acesso à API IPMA Open | Ter conexão à Internet para `api.ipma.pt` |
| Acesso à API Waze CCP | Capacidade de utilizar a API Waze CCP |

> **_NOTA:_** A interação com o Waze está atualmente indisponível.

# Configuração

O Data Bridge é configurável através de um ficheiro `config.toml`, que contém a
informação necessária para o programa carregar os módulos esperados.

A estrutura deste ficheiro é a seguinte:

| Definição | Tipo | Predefinição |
| ------- | ---- | ------- |
| Hono | Object | null | 
| Devices | Array | null | 

## Objeto Hono

No objeto Hono, os seguintes campos são definidos:

| Definição | Tipo | Predefinição | Descrição |
| ------- | ---- | ------- | ----------- |
| `http_adapter` | URL | https://localhost:8443 | URL do Adaptador HTTP da instância Hono a ser utilizada |
| `tenant_id` | String | "DEFAULT_TENANT" | ID do tenant para o qual as mensagens serão enviadas. O tenant DEVE já existir antes de o Data Bridge ser iniciado, caso contrário ocorrerá um erro. |
| `server_cert_path` | Path | null | Este campo é OPCIONAL. Contém o caminho para o certificado x509 do servidor, caso este seja necessário. |

Todas as
ligações feitas pelo Data Bridge ao Eclipse Hono são feitas através de HTTPS, e
o contexto SSL/TLS está ativado, o que significa que se o Data Bridge não conseguir verificar
o certificado apresentado pelo Adaptador HTTP, o programa irá parar. Para
evitar isto, no caso de o endpoint não conter um certificado x509 válido e
público, um certificado raiz pode ser passado para a aplicação usando `server_cert_path`.

## Array Devices

O array `devices` é uma lista contendo vários objetos `device`. Cada objeto
é definido da seguinte forma:

| Definição | Tipo | Predefinição | Descrição |
| ------- | ---- | ------- | ----------- |
| `cert_path` | Path | null | Caminho para o certificado x509 do dispositivo, usado para autenticar o dispositivo específico junto do Adaptador HTTP no Eclipse Hono. |
| `private_key` | Path | null | Caminho para a chave privada correspondente ao certificado. |
| `policy_id` | String | null | `policy` que o Eclipse Ditto irá aplicar sobre os comandos que o Data Bridge enviará através do Eclipse Hono. |
| `namespace` | str | null | Namespace a ser usado pelo dispositivo no Eclipse Ditto. |
| `strategies` | Array | [] | Explicado em maior detalhe na secção seguinte |

Os ThingIds no Eclipse Ditto seguem o padrão já estabelecido
`namespace:subject:id` já existente na infraestrutura. O
`namespace` é definido pelo dispositivo, e o dispositivo terá controlo sobre
apenas os Things neste namespace. Tem de corresponder ao campo `Common Name` do
certificado x509 fornecido.

## Strategies

A arquitetura deste programa baseia-se no conceito de `strategies`, que são um
módulo reutilizável que define que dados o dispositivo deve enviar para o Eclipse Ditto.

Cada strategy terá de definir pelo menos um `type`, que é o discriminador
entre as diferentes strategies, e um `subject`, que definirá a
parte `subject` do ThingId.

| Campo | Tipo | Descrição |
| ----- | ---- | ----------- |
| `type` | String | Discriminador da strategy a utilizar. |
| `subject` | String | Subject a ser utilizado no ThingId |

À data da escrita deste manual, existem as seguintes strategies:

- `meteo`
- `meteo_warnings`
- `type`
- `geojson`

### Strategy Meteorológica

A strategy `meteo` é responsável por consultar a [API
IPMA](https://api.ipma.pt) e criar/atualizar Things no Eclipse Ditto que
contenham os dados das várias estações meteorológicas que a IPMA disponibiliza.
Esta strategy criará Things com um ThingId formatado como
`namespace:subject:station_id`, onde `station_id` é um número fornecido pela
API da IPMA.

Para fazer com que um dispositivo utilize esta strategy, o seguinte objeto deve ser configurado e adicionado ao seu array `strategies`:

| Campo | Tipo | Descrição |
| ----- | ---- | ----------- |
| `type` | Literal | `meteo` |
| `subject` | String | Subject a ser utilizado no ThingId |

## Strategy de Avisos Meteorológicos

A strategy `meteo_warnings` é responsável por consultar a [API
IPMA](https://api.ipma.pt) e atualizar os Things de estações meteorológicas
existentes com uma nova funcionalidade `events` que conterá avisos meteorológicos conforme
fornecidos pela IPMA. Um determinado aviso será adicionado às 3 estações
meteorológicas mais próximas (num máximo de 100 km) da área do aviso.

Para fazer com que um dispositivo utilize esta strategy, o seguinte objeto deve ser configurado e adicionado ao seu array `strategies`:
| Campo | Tipo | Descrição |
| ----- | ---- | ----------- |
| `type` | Literal | `warnings` |
| `subject` | String | Subject a ser utilizado no ThingId |

## Strategy de Trânsito

> **_NOTA:_** À data da escrita deste manual, esta strategy não está a funcionar como
> pretendido e não deve ser ativada. É um componente legado e poderá ser
> atualizado no futuro.

A strategy `traffic` é responsável por, dada uma localização geográfica e um raio, simular
um Ponto Sensor nessa localização e publicar os dados de trânsito conforme retornados pelo Waze.
Aceita também um `sensor_name` que será usado no formato do ThingId.

Para fazer com que um dispositivo utilize esta strategy, o seguinte objeto deve ser configurado e adicionado ao seu array `strategies`:

| Campo | Tipo | Descrição |
| ----- | ---- | ----------- |
| `type` | Literal | `traffic` |
| `subject` | String | Subject a ser utilizado no ThingId |
| `sensor_name` | String | O nome do sensor a ser usado no formato do ThingId. | 
| `road` | String | O nome da estrada onde este sensor deve estar localizado. |
| `latitude` | Float | A latitude geográfica, em WGS84, onde o sensor estará localizado. |
| `longitude` | Float | A longitude geográfica, em WGS84, onde o sensor estará localizado. |
| `radius` | Integer | O raio (em metros) que o sensor usará para consultar a API do Waze para obter `alerts` e `jams` |

## Strategy GeoJSON

A strategy `geojson` é responsável por, dado um caminho GeoJSON OU diretório
contendo ficheiros GeoJSON, recuperar todas as features desse GeoJSON e
criar um Thing do Eclipse Ditto com a informação contida nas `properties`,
`coordinates` no caso de um ponto único, ou `geometry` no caso de
vários pontos.

> **_NOTA:_** À data da escrita deste manual, esta strategy espera que a
> informação geográfica no GeoJSON seja expressa na projeção ETRS89,
> e converte-a automaticamente para a projeção WGS84. Isto poderá
> mudar no futuro, e a strategy poderá ser atualizada para recuperar
> automaticamente a projeção original do ficheiro GeoJSON. O resultado será
> sempre em WGS84.

Para fazer com que um dispositivo utilize esta strategy, o seguinte objeto deve ser configurado e adicionado ao seu array `strategies`:
| Campo | Tipo | Descrição |
| ----- | ---- | ----------- |
| `type` | Literal | `geojson` |
| `subject` | String | Subject a ser utilizado no ThingId |
| `file` | Path | A localização do ficheiro para a strategy ler |
| `dir` | Path | A localização do diretório que contém os ficheiros GeoJSON para a strategy ler |

É importante notar que estes campos são MUTUAMENTE EXCLUSIVOS, ou seja,
se `file` estiver definido, `dir` deve estar não definido e vice-versa.

## Uma nota sobre geotiles

De acordo com o padrão existente do sistema, este Data Bridge adiciona um `expiry_ts` e um
`geotile` a todos os Things que cria, onde o primeiro é uma dica para o
coletor de lixo sobre se um Thing deve ou não ser eliminado, enquanto o segundo
é um atributo que permite a pesquisa geográfica rápida de Things numa
determinada área (um geotile). A implementação destes geotiles pode ser vista em [docs/geotile.md](geotile.md)

# Guia de deployment

O Data Bridge é uma aplicação Python. No entanto, pode ser implantado de 3 formas diferentes:
- Instanciação direta da aplicação
- Utilização do contentor Docker fornecido
- Utilização de um Helm chart (para deployment em Kubernetes)

No entanto, é importante notar que a aplicação fornecida executará uma
única execução, dado que se destina a funcionar como um processo periódico,
ou seja, é instanciada periodicamente. Como tal, o Helm chart fornecido
é o método recomendado para deployment, pois será automaticamente
configurado como um Kubernetes CronJob. No caso dos outros métodos de
deployment, este comportamento deve ser configurado manualmente usando outras ferramentas (como
CronJobs nativos do Linux).

## Instanciação direta

A aplicação Python foi desenvolvida num ambiente gerido por
[uv](https://docs.astral.sh/uv). No entanto, é compatível com PEP-518, o que significa que a ferramenta
`uv` não é necessária para executar a aplicação, pois as dependências podem ser geridas
e instaladas usando `pip` num ambiente virtual configurado, ou `venv`.

Utilizar a instanciação direta é tão simples como executar o ficheiro
[main.py](../main.py) no ambiente gerido (quer usando `uv run main.py` se usar `uv`
ou executando `python main.py` no `venv` se usar qualquer outra ferramenta
compatível com PEP-518).

Neste caso, o ficheiro de configuração `config.toml` deve ser colocado na raiz
do projeto, que será o diretório onde o ficheiro `main.py` está
localizado. O Data Bridge carregará automaticamente esse ficheiro e aplicará as
configurações nele contidas. Para detalhes sobre como configurar o Data Bridge,
consulte o [guia do utilizador](./user.md). Adicionalmente, dado que este projeto
utiliza `pydantic-settings`, estas também podem ser definidas usando variáveis de
ambiente. Estas são nomeadas exatamente como os campos, usando um duplo underscore
(`__`) para objetos aninhados. Por exemplo, o campo `http_adapter` do objeto Hono
é definido como `HONO__HTTP_ADAPTER`. Para definir arrays e tipos mais
complexos, pode ser usada uma string codificada em JSON. Como exemplo, para definir um dispositivo,
pode ser usada a seguinte variável de ambiente:
```json
DEVICES="[
  {
    cert_path:<path>,
    private_key:<path>,
    policy_id:<str>,
    namespace:<str>,
    strategies:[
      {
        type:<str>,subject:<str>,
      },
    ]
  }  
]"
```

## Docker file

A utilização do Docker file é mais simples do que a instanciação direta, pois a
imagem apenas precisa de ser construída (ou usar a imagem pré-construída em
`atnog-harbor.av.it.pt/dt4mob/data-bridge`), montando o ficheiro `config.toml` no
diretório `/app/config.toml`.

Isto pode ser feito com o comando `docker run -v config.toml:/app/config.toml
atnog-harbor.av.it.pt/dt4mob/data-bridge`. Recorda-se novamente que isto
executará uma única execução do Data Bridge, e apenas atualizará os
things uma vez. O comportamento de execução periódica fica a cargo da
pessoa administradora.

Adicionalmente, tal como na instanciação direta, a configuração pode ser feita
com variáveis de ambiente.

Quaisquer outros ficheiros que possam ser necessários ao Data Bridge (como no caso da
strategy `geojson`) também devem ser montados no contentor Docker, e no
caminho configurado no ficheiro de configuração `config.toml`. Este caminho DEVE ser
igual ao caminho do ficheiro dentro do Contentor Docker, e não o da
máquina anfitriã.

## Helm Chart

O Helm chart está disponível no [repositório GitHub
dt4mob-platform](https://github.com/ATNoG/dt4mob-platform) e pode ser instalado
usando o instalador Helm (`helm install data-bridge <location_of_chart> -f <location_of_values.yml>`)
A configuração neste caso é feita através do ficheiro `values.yml`, mas segue
a mesma estrutura do ficheiro de configuração `config.toml`.

Quaisquer outros ficheiros que possam ser necessários ao Data Bridge (como no caso da
strategy `geojson`) devem ser montados no pod Kubernetes, e no
caminho configurado no ficheiro de configuração `values.yml`.
