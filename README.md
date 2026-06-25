# Data Bridge

Data Bridge is a data integration service that polls
multiple road and meteorological data sources (IPMA, Waze, and local GeoJSON
files) and forwards the normalized data to an Eclipse Hono IoT device registry
using the Eclipse Ditto protocol over HTTP.

## Prerequisites

Python ≥ 3.13 (required by the project manifest).

A running Eclipse Hono instance accessible over HTTP, with a working HTTP Adapter endpoint.
Network access to the IPMA Open API (api.ipma.pt) for meteorological data.
Network access to the Waze CCP Traffic Data API for traffic and incident data.

> **_NOTE:_**  The interaction with Waze is currently unavailable.

# User's Manual

This document contains the instructions on how to use the Data Bridge, namely
how to configure the different required aspects and what their functionality
is.

It can be found in [docs/user.md](docs/user.md)

# Programmer's Manual

This section contains the instructions on how to expand the Data Bridge, namely
how to add support for more devices and data sources.

It can be found in [docs/user.md](docs/programmer.md)

# Administrator Manual

This section contains the instructions on how to deploy the Data Bridge,
especially how it is packaged as either a Docker container or a Helm chart for
deployment in a Kubernetes Cluster.

It can be found in [docs/user.md](docs/admin.md)
