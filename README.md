# IoT Weather and Traffic Data Bridge

This project is an asynchronous data bridge that collects meteorological data from **IPMA** (the Portuguese Institute for Sea and Atmosphere) and traffic data from **Waze**. It then forwards this information to an IoT platform through **Eclipse Hono**, formatted for **Eclipse Ditto**.

The application runs as a **FastAPI** service with background tasks that periodically poll the data sources.

## Core Functionality

  * **Periodic Data Fetching**: Automatically fetches updated weather and traffic data at a configurable interval.
  * **External API Integration**:
      * Pulls meteorological observations from IPMA's public GeoJSON feed.
      * Retrieves traffic jams and alerts from the Waze Live Map API for predefined locations.
  * **IoT Platform Integration**:
      * Registers and authenticates devices with an Eclipse Hono instance.
      * Sends telemetry data, formatted as a **Ditto Protocol Envelope** create/modify command, allowing for Digital Twin creation and update.

-----

## How It Works

The application operates in two main phases: startup and periodic updates.

### 1\. Application Startup

1.  **Load Configuration**: On startup, the application reads its configuration from `config.toml` using the `pydantic-settings` library (`settings.py`). This includes Hono credentials, polling intervals, and lists of devices and traffic sensor locations (`tolls`).
2.  **Initialize Singletons**: It sets up singleton instances for managing the `aiohttp` client session, a list of known weather stations, and the device clients (`storage/__init__.py`).
3.  **Create Hono Devices**: It iterates through the devices listed in `config.toml`. For each one, it creates a `HonoDevice` instance (`interfaces/hono.py`).
4.  **Register with Hono**: The `create_hono_device()` method is called for each device. This sends a `POST` request to the Hono device registry and sets up hashed-password credentials. If a device already exists (HTTP 409 Conflict), it skips creation.
5.  **Instantiate Device Logic**: Based on the device `type` (`meteo` or `traffic`), it wraps the `HonoDevice` connection in a `MeteoDevice` or `TrafficDevice` class and stores it in the `DevicesSingleton`.
6.  **Initial Data Fetch**: It runs the `update_meteo` and `update_traffic` tasks, starting their periodic execution.

### 2\. Periodic Updates

The application runs two background tasks concurrently, controlled by `@repeat_every` in `main.py`.

#### Meteorology Data Flow (`update_meteo`)

1.  **Fetch Data**: The task calls `get_measurements()` from `interfaces/ipma.py` , which makes an HTTP request to the IPMA GeoJSON endpoint.
2.  **Filter and Parse**: It parses the response, keeping only the most recent measurements and modeling the data into `Station` and `Measurement` Pydantic objects.
3.  **Update Station Cache**: The list of active weather stations is updated in the `StationSingleton`, keeping it available for querying by the `\meteorology` endpoint
4.  **Send Telemetry**: The task retrieves the `MeteoDevice`  and iterates through each station and its corresponding measurement.
5.  **Format for Ditto**: For each station, `meteo.modify()` is called. This formats the data into a Ditto Protocol message. The message follows the [create/modify command](https://eclipse.dev/ditto/protocol-specification-things-create-or-modify.html), meaning that if the Digital Twin already exists in Ditto, it will just be updated, but if it is non-existing, then it will be created.
6.  **Transmit via Hono**: The formatted message is sent to the Hono HTTP adapter's telemetry endpoint. Ditto will then consume this message from the connection that it has with the Hono instance

#### Traffic Data Flow (`update_traffic`)

1.  **Iterate Sensor Points**: The task loops through the list of traffic sensor points (`tolls`) defined in `config.toml`.
2.  **Fetch Data**: For each sensor point's latitude and longitude, it calls `get_traffic_data()` from `interfaces/waze.py`. This function calculates a rectangular bounding box around the point  and queries the Waze API.
3.  **Process in Parallel**: These API calls are run concurrently using `asyncio.gather()`.
4.  **Send Telemetry**: The task retrieves the `TrafficDevice` and iterates through each toll and its corresponding Waze data.
5.  **Format for Ditto**: For each toll, `traffic.modify()` is called.
      * It finds the 3 closest weather stations using `StationSingleton.get_closest_stations()` and adds their IDs to the Ditto Thing's `attributes`.
      * It includes the toll's location and name as attributes.
      * It places the Waze alert and jam data into the `properties` of a feature named `traffic`.
6.  **Transmit via Hono**: The formatted message is sent to the Hono HTTP adapter's telemetry endpoint. Ditto will then consume this message from the connection that it has with the Hono instance

-----

## Configuration (`config.toml`)

The application is configured via the `config.toml` file.

  * **`env`**: `dev` or `prod`. In `prod` mode, SSL verification is enabled for Hono requests.
  * **`polling_interval`**: The time in seconds between each data fetch cycle.
  * **`[hono]`**:
      * `device_registry`: The base URL for the Hono device registry API.
      * `http_adapter`: The URL for the Hono HTTP telemetry adapter.
      * `tenant_id`: The Hono tenant ID to use for all devices.
  * **`[[devices]]`**: A list of logical devices to register with Hono.
      * `type`: Must be `"meteo"` or `"traffic"`.
      * `policy_id`: The Ditto Policy ID to associate with the device's twin.
      * `passwd`: The password for the device.
  * **`[[tolls]]`**: A list of traffic sensor locations. Each entry defines a point for which traffic data will be fetched.
      * `name`: A unique name for the sensor point.
      * `road`, `latitude`, `longitude`: Location information.
      * `area_radius`: The radius in meters around each sensor point to query the Waze API.

-----

## Extending the Codebase

### How to Add a New Data Source (e.g., Air Quality)

To add a new data source, you'll need to create a new interface, a new device class, and update the main application logic.

1.  **Define Data Models (`models/`)**:

      * Create a `models/air_quality.py` file.
      * Define Pydantic models for the data you'll be fetching (e.g., `AirQualityDevice`, `AirQualityReading`).

2.  **Create an API Interface (`interfaces/`)**:

      * Create an `interfaces/air_quality.py` file.
      * Write an `async` function (e.g., `get_air_quality_data()`) that uses the `SessionSingleton` to fetch data from the new API endpoint and returns your Pydantic models.

3.  **Create a Device Class (`devices/`)**:

      * Create a `devices/air_quality.py` file.
      * Define a new class `AirQualityDevice(Device)` that inherits from the base `Device` class in `devices/ditto.py`.
      * Implement the `async def modify(self, device, data)` method. This method should:
          * Define any `attributes` and `features` needed for the Ditto twin.
          * Call `self.modify_message(device, data)` to construct the Ditto Protocol envelope.
          * Call `await self._hono.send_telemetry(message)` to send the data.

4.  **Update Configuration (`settings.py` and `config.toml`)**:

      * In `settings.py`, add `"air_quality"` to the `DeviceType` enum.
      * In `config.toml`, add a new device entry:
        ```toml
        [[devices]]
        type = "air_quality"
        policy_id = "<hono-policy-id>"
        passwd = "<hono-device-password>"
        ```

5.  **Update Main Application Logic (`main.py`)**:

      * Import your new device and interface.
      * In the `DeviceSingleton`, add a new case to the `match` statement to instantiate your `AirQualityDevice`.
      * Create a new periodic task function, `update_air_quality()`, decorated with `@repeat_every`. This function will call your data fetch function defined in the new interface and then call the `modify` method on your `AirQualityDevice` instance.
      * Call your new task in the `lifespan` function after device creation: `await update_air_quality()`.
