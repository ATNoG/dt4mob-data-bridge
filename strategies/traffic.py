from typing import List, final

from interfaces.waze import get_traffic_data
from models.ditto import CommandAction, DittoProtocolEnvelope, Feature
from strategies.strategy import BaseStrategy
from utils.geo import get_geotile


@final
class TrafficStrategy(BaseStrategy):
    def __init__(
        self,
        namespace: str,
        subject: str,
        policyId: str,
        sensorName: str,
        road: str,
        latitude: float,
        longitude: float,
        radius: float = 1000,
    ):
        super().__init__(namespace, subject, policyId)

        self.sensorName = sensorName
        self.road = road
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius

    async def get_telemetry(self) -> List[DittoProtocolEnvelope]:
        data = await get_traffic_data(self.latitude, self.longitude, self.radius)

        modify_topic = self._create_topic(self.sensorName)
        geotile = get_geotile(self.latitude, self.longitude, 31)
        attributes = {
            "sensorName": self.sensorName,
            "road": self.road,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "radius": self.radius,
            "geotile": geotile,
        }
        thing = self._create_envelope(modify_topic, attributes)
        envelopes = [thing]

        envelopes.append(self._create_alert_feature(data))
        envelopes.extend(self._create_jams_features(data))

        return envelopes

    def _create_alert_feature(self, data) -> DittoProtocolEnvelope:
        merge_topic = self._create_topic(self.sensorName, action=CommandAction.MERGE)
        alert_feature = Feature(properties={"alerts": data.alerts})
        alert_envelope = self._create_envelope_raw(
            merge_topic, value=alert_feature, path="/features/alerts"
        )

        return alert_envelope

    def _create_jams_features(self, data) -> List[DittoProtocolEnvelope]:
        envelopes = []
        merge_topic = self._create_topic(self.sensorName, action=CommandAction.MERGE)

        for i, jam in enumerate(data.jams):
            jam_feature = Feature(properties={str(i): jam})

            # TODO: create enough features to maximize the data limit of Hono, reducing the total messages that need to be sent

            jam_envelope = self._create_envelope_raw(
                merge_topic, value=jam_feature, path="/features/alerts"
            )
            envelopes.append(jam_envelope)

        return envelopes
