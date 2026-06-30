from datetime import datetime, timedelta, timezone
from typing import List, final

from loguru import logger

from interfaces.ipma import get_meteorology_measurements, get_meteorology_warnings
from models.ditto import DittoProtocolEnvelope, Feature
from models.meteo import Measurement, Station
from strategies.strategy import BaseStrategy
from utils.geo import get_geotile


@final
class MeteoStrategy(BaseStrategy):
    async def get_telemetry(self) -> List[DittoProtocolEnvelope]:
        logger.info("Acquiring metereology stations' information")
        measurements = await get_meteorology_measurements()
        logger.debug(
            "Acquiring metereology stations' information, creating message envelopes"
        )

        envelopes = [self.envelope_from_measurement(tup) for tup in measurements]

        logger.debug("Metereology stations' message envelopes created successfully")
        return envelopes

    def envelope_from_measurement(
        self,
        tup: tuple[Station, Measurement],
    ) -> DittoProtocolEnvelope:
        station, measurement = tup
        attributes = station.model_dump()
        geotile = get_geotile(station.location.latitude, station.location.longitude, 31)
        attributes["geotile"] = geotile
        attributes["expiry_ts"] = (
            datetime.now(timezone.utc) + timedelta(days=1)
        ).isoformat()
        features = {"meteorology": Feature(properties=measurement.model_dump())}
        topic = self._create_topic(str(station.id))
        return self._create_envelope(topic, attributes, features)


class WarningsStrategy(BaseStrategy):
    async def get_telemetry(self) -> List[DittoProtocolEnvelope]:
        logger.info("Acquiring metereology stations' warnings")
        warnings = await get_meteorology_warnings()

        logger.debug("Meteorology warnings acquired, creating message envelopes")
        ret = []
        for station, warning in warnings.items():
            dump = [warn.model_dump() for warn in warning]
            path = "/features/events"
            feature = {"properties": {"warnings": dump}}
            topic = self._create_topic(str(station.id))
            ret.append(self._create_envelope_raw(topic, feature, path))

        logger.debug("Meteorology warning message envelopes created successfully")

        return ret
