from typing import List, final

from loguru import logger

from interfaces.ipma import get_meteorology_measurements
from models.ditto import DittoProtocolEnvelope, Feature
from models.meteo import Measurement, Station
from strategies.strategy import BaseStrategy
from utils.geo import get_geotile


@final
class MeteoStrategy(BaseStrategy):
    async def get_telemetry(self) -> List[DittoProtocolEnvelope]:
        logger.info("Updating metereology stations' information")
        measurements = await get_meteorology_measurements()
        logger.debug("Got measurements from IPMA")

        return [self.envelope_from_measurement(tup) for tup in measurements]

    def envelope_from_measurement(
        self,
        tup: tuple[Station, Measurement],
    ) -> DittoProtocolEnvelope:
        station, measurement = tup
        attributes = station.model_dump()
        geotile = get_geotile(station.location.latitude, station.location.longitude, 31)
        attributes["geotile"] = geotile
        features = {"meteorology": Feature(properties=measurement.model_dump())}
        topic = self.create_topic(str(station.id))
        return self.create_envelope(topic, attributes, features)
