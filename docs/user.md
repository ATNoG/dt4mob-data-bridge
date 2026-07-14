# Data Bridge

Data Bridge is a data integration service that polls
multiple road and meteorological data sources (IPMA, Waze, and local GeoJSON
files) and forwards the normalized data to an Eclipse Hono IoT device registry
using the Eclipse Ditto protocol over HTTP.

## Prerequisites

Before using the Data Bridge, ensure you have:

| Requirement | Version/Details |
| ----------- | --------------- |
| Python      | 3.13 or higher  |
| Eclipse Hono | Instance with a configured HTTP adapter using cert-based authentication |
| Python virtual environment | A configured virtual environment, either using `uv` or any other PEP-518 compliant system |
| IPMA Open API access | Have internet connection to `api.ipma.pt` |
| Waze CCP API access | Ability to use the Waze CCP API |

> **_NOTE:_** The interaction with Waze is currently unavailable.

# Configuration

The Data Bridge is configurable through a `config.toml` file, which contains the
needed information for the program to load the expected modules.

The structure of this file is as follows:

| Setting | Type | Default |
| ------- | ---- | ------- |
| Hono | Object | null | 
| Devices | Array | null | 

## Hono Object

In the Hono object, the following fields are set:

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `http_adapter` | URL | https://localhost:8443 | URL of the HTTP Adapter of the Hono instance to be used |
| `tenant_id` | String | "DEFAULT_TENANT" | Tenant ID to which the messages will be sent. . The tenant MUST already exist before the Data Bridge is started, else it will error. |
| `server_cert_path` | Path | null | This field is OPTIONAL. Contains the path to the server x509 certificate, in the case that it may be required. |

All the
connections made by the Data Bridge to Eclipse Hono are made via HTTPS, and
the SSL/TLS context is enabled, meaning that if the Data Bridge cannot verify
the certificate presented by the HTTP Adapter, the program will halt. To
avoid this, in the case that the endpoint does not contain a valid, public
x509 certificate, a root certificate can be passed to the app using `server_cert_path`

## Devices Array

The `devices` array is a list containing several `device` objects. Each object
is defined as follows:

| Setting | Type | Default | Description |
| ------- | ---- | ------- | ----------- |
| `cert_path` | Path | null | Path to the device's x509 certificate, used for authenticating the specific device with the HTTP Adapter in Eclipse Hono. |
| `private_key` | Path | null | Path to the certificate's corresponding private key. |
| `policy_id` | String | null | `policy` that Eclipse Ditto will enforce over the commands that the Data Bridge will send over Eclipse Hono. |
| `subject` | str | null | Subject to be used by the device in Eclipse Ditto. |
| `strategies` | Array | [] | Explained in higher detail in the following section |

The ThingIds in Eclipse Ditto follow the already established
`namespace:subject:id` pattern already existing in the infrastructure. The
`subject` is defined by the device, and the device will have control over
only the Things on this namespace. It has to match the `Common Name` field of
the provided x509 certificate.



## Strategies

This program's architecture is based on what is called `strategies`, which is a
reusable module that defines what data the device should send to Eclipse Ditto.

Each strategy will have to define at least a `type`, which is the discriminator
among the different strategies, and a `namespace`, which will define the
`namespace` part of the ThingId.

| Field | Type | Description |
| ----- | ---- | ----------- |
| `type` | String | Discriminator of the strategy to use. |
| `namespace` | String | Namespace to be used in the ThingId |

As of writing this manual, the following strategies exist:

- `meteo`
- `meteo_warnings`
- `type`
- `geojson`

### Meteorologic Strategy

The `meteo` strategy is responsible for querying the [IPMA
API](https://api.ipma.pt) and creating/updating Things in Eclipse Ditto that
contain the data of the several meteorologic stations that IPMA provides.
This strategy will create Things with a ThingId formatted as
`namespace:subject:station_id`, where `station_id` is a number given by IPMA's
API.

To make a device use this strategy, the following object must be configured and added to it's `strategies` array:

| Field | Type |  Description |
| ----- | ---- | ----------- |
| `type` | Literal | `meteo` |
| `namespace` | String | Namespace to be used in the ThingId |

## Meteorologic Warnings Strategy

The `meteo_warnings` strategy is responsible for querying the [IPMA
API](https://api.ipma.pt) and updating the existing meteorologic station Things
with a new feature `events` that will contain meteorologic warnings as provided
by IPMA. A given warning will be added to the 3 closest meteorologic stations
(within a maximum of 100 km) of the warning's area.

To make a device use this strategy, the following object must be configured and added to it's `strategies` array:
| Field | Type | Description |
| ----- | ---- | ----------- |
| `type` | Literal | `warnings` |
| `namespace` | String | Namespace to be used in the ThingId |

## Traffic Strategy

> **_NOTE:_** As of writing this manual, this strategy is not working as
> intended and should not be enabled. It is a legacy component and may be
> updated in the future.

The `traffic` strategy is responsible for, given a geographic location and radius, emulate
a Sensor Point in that location and publishing the traffic data as returned by Waze.
It also accepts a `sensor_name` that will be used in the format of the ThingId.


To make a device use this strategy, the following object must be configured and added to it's `strategies` array:

| Field | Type |  Description |
| ----- | ---- |  ----------- |
| `type` | Literal | `traffic` |
| `namespace` | String | Namespace to be used in the ThingId |
| `sensor_name` | String | The sensor's name to be used in the ThingId format. | 
| `road` | String | The name of the road that this sensor is meant to be located. |
| `latitude` | Float |  The geographical latitude, in WGS84, that the sensor will be located. |
| `longitude` | Float |  The geographical longitude, in WGS84, that the sensor will be located. |
| `radius` | Integer |  The radius (in meters) that the sensor will query Waze's API for getting `alerts` and `jams` |

## GeoJSON strategy

The `geojson` strategy is responsible for, given a GeoJSON path OR directory
containing GeoJSON files, retrieve all the features inside that GeoJSON and
create an Eclipse Ditto Thing with information contained in the `properties`
`coordinates` in the case of a single point, or `geometry` in the case of
multiple points. 

> **_NOTE:_** As of writing this manual, this strategy expects the
> geographical information in the GeoJSON to be expressed in the ETRS89
> projection, and automatically converts it to the WGS84 projection. This might
> change in the future, and the strategy may be updated to automatically
> retrieve the original projection from the GeoJSON file. The output will be
> always in WGS84.

To make a device use this strategy, the following object must be configured and added to it's `strategies` array:
| Field | Type | Description |
| ----- | ---- | ----------- |
| `type` | Literal | `geojson` |
| `namespace` | String | Namespace to be used in the ThingId |
| `file` | Path | The location of the file for the strategy to read |
| `dir` | Path | The location of the directory that contains the GeoJSON files for the strategy to read |

It is important to note that these fields are MUTUALLY EXCLUSIVE, meaning that
if `file` is set, `dir` must be unset and vice-versa.

## A note on geotiles

As per the system's existing standard, this Data Bridge adds a `expiry_ts` and a
`geotile` to all the Things it creates, where the first is a hint to the
garbage collector of whether a Thing is or not to be deleted, while the second
is an attribute that allows for the quick geographical search of Things within
a given area (a geotile). The implementation of these geotiles can be seen in [docs/geotile.md](geotile.md)

# Deployment guide

The Data bridge is a Python application. However, it can be deployed in 3 different ways:
- Direct instantiation of the application
- Utilization of the provided Docker container
- Utilization of a Helm chart (for deployment in Kubernetes)

However, it is important to note that the provided application will perform a
single execution, given that it is intended to work as a periodic process,
meaning that it is instantiated periodically. As such, the provided Helm chart
is the recommended method for deployment, as it will automatically be
configured as a Kubernetes CronJob. In the case of the other deployment
methods, this behavior must be manually configured using other tools (such as
native Linux cronjobs)

## Direct instantiation

The python application was developed in a [uv](https://docs.astral.sh/uv)
managed environment. However, it is PEP-518 compliant, meaning that the `uv`
tool is not required to run the application, as the dependencies can be managed
and installed by using `pip` in a configured virtual environment, or `venv`.

Using direct instantiation is as simple as running the [main.py](../main.py)
file in the managed environment (by either using `uv run main.py` if using `uv`
or by running `python main.py` in the `venv` if using any other PEP-518
compliant tool).

In this case, the `config.toml` configuration file must be placed in the root
of the project, which will be the directory where the `main.py` file is
located. The Data Bridge will automatically load that file and apply the
configurations within it. For details on how to configure the Data Bridge,
refer to the [user guide](./user.md). Additionally, given that this project
utilizes `pydantic-settings`, these can also be set using environment
variables. These are named just like the fields, using a double underscore
(`__`) for nested objects. For example, the Hono object's `http_adapter` object
is defined as `HONO__HTTP_ADAPTER`. For defining arrays and more complex
types, a JSON encoded string can be used. As an example, for defining a device,
the following environment variable can be used:
```json
DEVICES="[
  {
    cert_path:<path>,
    private_key:<path>,
    policy_id:<str>,
    subject:<str>,
    strategies:[
      {
        type:<str>,namespace:<str>,
      },
    ]
  }  
]"
```

## Docker file 

The usage of the docker file is simpler than the direct instantiation, as the
image only needs to be built (or use the pre-built image in
`atnog-harbor.av.it.pt/dt4mob/data-bridge`), mounting the `config.toml` file in
the directory `/app/config.toml`

This can be done with the command `docker run -v config.toml:/app/config.toml
atnog-harbor.av.it.pt/dt4mob/data-bridge`. It is once again reminded that this
will perform a single execution of the Data Bridge, and will only update the
things once. The periodic execution behavior is left for implementation by the
administrator.

Additionally, like with the direct instantiation, the configuration can be made
with environment variables.

Any other files that may be required by the Data Bridge (such as in the case of
the `geojson` strategy) must also be mounted on the Docker container, and in
the path configured in the `config.toml` configuration file. This path MUST be
equal to the path of the file inside the Docker Container, and not that of
the host.

## Helm Chart

The helm chart is available at the [dt4mob-platform GitHub
repository](https://github.com/ATNoG/dt4mob-platform) and can be installed
using the Helm installer (`helm install data-bridge <location_of_chart> -f <location_of_values.yml>`)
The configuration in this case is done via the `values.yml` file, but follows
the same structure of the `config.toml` configuration file.

Any other files that may be required by the Data Bridge (such as in the case of
the `geojson` strategy) must be mounted on the Kubernetes pod, and in
the path configured in the `values.yml` configuration file.
