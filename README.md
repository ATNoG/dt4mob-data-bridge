# Data Bridge

Data Bridge is a FastAPI-based data integration service that continuously polls
multiple road and meteorological data sources (IPMA, Waze, and local GeoJSON
files) and forwards the normalized data to an Eclipse Hono IoT device registry
using the Eclipse Ditto protocol over HTTP.

## Overview

The service acts as a bridge between external data sources and a Hono/Ditto IoT
platform. On startup, it auto-registers the configured virtual devices in
Hono's Device Registry and immediately executes a first data sync cycle. Five
device types are managed: meteo (meteorological stations from IPMA), traffic
(Waze-sourced road incidents), sign (road sign inventory from GeoJSON), barrier
(road barrier inventory from GeoJSON), and equivia (road infrastructure
features from GeoJSON).

## Prerequisites

Python ≥ 3.13.5 (required by the project manifest).

A running Eclipse Hono instance accessible over HTTP, with a working Device Registry endpoint and an HTTP Adapter endpoint.

Local GeoJSON data files for signs, barriers, and Equivia road features, organized in directories as described below.

Network access to the IPMA Open API (api.ipma.pt) for meteorological data.

Network access to the Waze CCP Traffic Data API for traffic and incident data.

## Installation

Clone or copy the project source to your machine. The project uses
pyproject.toml for dependency management, so you can install it with any PEP
517-compliant tool. Using uv (recommended) or pip:

```bash
# Using uv (recommended)
uv sync

# Using pip with a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install .
```

For development, install the dev dependency group as well, which includes ruff (linter), ty (type checker), and pre-commit hooks:


```bash
uv sync --group dev
pre-commit install
```

## Configuration

All configuration is loaded from config.toml, placed in the working directory
from which the service is launched. Environment variables can also override any
setting using double-underscore (__) as a nested delimiter (e.g.,
HONO__TENANT_ID=my-tenant). Environment variables take precedence over the TOML
file.

### Top-level keys

| Key              | Type              | Default | Description                                                                          |
| ---------------- | ----------------- | ------- | -----------------------------------------------------------------------------------  |
| env              | "prod" or "dev"   | "prod"  | Runtime environment. In dev, SSL verification is disabled for Hono requests. hono.py |
| polling_interval | integer (seconds) | 3600    | How often the service polls data sources in its background loops. settings.py        |


### `[Hono]` section

This section configures the connection to your Eclipse Hono instance.

| Key              | Default                | Description                                                              |
| ---------------- | ---------------------- | ------------------------------------------------------------------------ |
| device_registry  | http://localhost:28443 | Base URL of the Hono Device Registry REST API.                           |
| http_adapter     | http://localhost:8443  | Base URL of the Hono HTTP Adapter for telemetry publishing.              |
| tenant_id        | "DEFAULT_TENANT"       | The Hono tenant identifier under which devices are registered.           |
| server_cert_path | null                   | Optional path to the Hono server's CA certificate for mTLS verification. |


### `[[devices]]` array

Each entry in the [[devices]] array declares one logical IoT device that the
service registers in Hono and uses to publish telemetry. Exactly one
authentication method must be specified per device, either passwd
(password-based) or cert_path (client certificate), never both.

| Key       | Description                                                                                     |
| --------- | ----------------------------------------------------------------------------------------------- |
| type      | Device type: one of traffic, meteo, sign, barrier, or equivia.                                  |
| policy_id | The Ditto policy ID to associate with the device upon creation.                                 |
| passwd    | Plaintext password. The service hashes it using SHA-512 before registering it in Hono. hono.py  |
| cert_path | Path to a PEM client certificate file for certificate-based authentication.                     |

### `[[tolls]]` array

Each entry defines a geospatial sensor point used for Waze traffic queries. The
service queries Waze for traffic events (jams, alerts, hazards) within a radius
around each defined coordinate.

| Key                  | Description                                                              |
| -------------------- | ------------------------------------------------------------------------ |
| name                 | A human-readable identifier for the sensor point.                        |
| road                 | The road or highway name (informational).                                |
| latitude / longitude | WGS-84 coordinates of the sensor point.                                  |
| area_radius          | Radius in metres to query around the point (default: 1000). settings.py  |

### `[signs]`, `[barriers]`, `[equivia]` sections

| Key          | Description                                                               |
| ------------ | ------------------------------------------------------------------------- |
| signs.dir    | Path to a directory containing road sign GeoJSON files.                   |
| barriers.dir | Path to a single GeoJSON file containing road barrier features.           |
| equivia.dir  | Path to a directory containing Equivia road infrastructure GeoJSON files. |

Equivia GeoJSON data must use the EPSG:3763 (PT-TM06) projected coordinate
system; the service converts all coordinates to WGS-84 (EPSG:4326)
automatically.

### Full example `config.toml`

```toml
env = "dev"
polling_interval = 900

[hono]
device_registry = "https://your-hono-host:31947"
http_adapter   = "https://your-hono-host:30501"
tenant_id      = "my-tenant"
# server_cert_path = "/etc/ssl/hono-ca.pem"  # optional

[[devices]]
type      = "meteo"
policy_id = "meteo:default"
passwd    = "a-strong-password"

[[devices]]
type      = "traffic"
policy_id = "traffic:default"
passwd    = "a-strong-password"

[[devices]]
type      = "sign"
policy_id = "signs:default"
passwd    = "a-strong-password"

[[devices]]
type      = "barrier"
policy_id = "signs:default"
passwd    = "a-strong-password"

[[devices]]
type      = "equivia"
policy_id = "signs:default"
passwd    = "a-strong-password"

[signs]
dir = "data/Signs"

[barriers]
dir = "data/Barriers/Barreiras.geojson"

[equivia]
dir = "data/Equivia"

[[tolls]]
name      = "SensorPoint1"
road      = "VCI"
latitude  = 41.1453611
longitude = -8.5811944
```

## Running the service

The service is a standard FastAPI application. Run it with the Uvicorn ASGI server included in the `fastapi[standard]` installation:

```sh
# From the project root (where config.toml lives)
uv fastapi run main.py
```

On startup, the lifespan handler will:

1. Register all configured devices in Hono (skipping any that already).

2. Fetch IPMA warning areas and populate the station cache.

3. Execute an immediate full sync of meteorological measurements and warnings.

## REST API

The service exposes one HTTP endpoint after startup:

```
GET /meteorology?lat={latitude}&lon={longitude}
```

Returns a list of Ditto Thing IDs for the IPMA weather stations geographically
closest to the provided coordinates. Returns HTTP 503 if no stations are loaded
(e.g., if the meteo device is not configured).

## Startup Behaviour & Batch Rate-Limiting

When pushing large datasets (signs, barriers, Equivia), the service sends up to
100 requests before pausing for 5 seconds to avoid overwhelming the Hono HTTP
adapter. This cooldown is applied automatically and requires no configuration.
For barrier updates an additional 10 ms sleep is inserted between individual
requests.
