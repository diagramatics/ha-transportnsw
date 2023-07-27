"""Support for Transport NSW (AU) to query next leave event."""
from __future__ import annotations

import logging
from typing import Any, List

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

ATTR_DUE_IN = "due"
ATTR_STOP_ID = "stop_id"
ATTR_ORIGIN_NAME = "origin_name"
ATTR_DEPARTURE_TIME = "departure_time"
ATTR_DESTINATION_STOP_ID = "destination_stop_id"
ATTR_DESTINATION_NAME = "destination_name"
ATTR_ARRIVAL_TIME = "arrival_time"
ATTR_ORIGIN_TRANSPORT_TYPE = "origin_transport_type"
ATTR_ORIGIN_TRANSPORT_NAME = "origin_transport_name"
ATTR_ORIGIN_LINE_NAME = "origin_line_name"
ATTR_ORIGIN_LINE_NAME_SHORT = "origin_line_name_short"
ATTR_CHANGES = "changes"
ATTR_OCCUPANCY = "occupancy"
ATTR_REAL_TIME_TRIP_ID = "real_time_trip_id"
ATTR_LATITUDE = "latitude"
ATTR_LONGITUDE = "longitude"

# CONF_STOP_ID = "stop_id"
# CONF_DESTINATION_STOP_ID = "destination_stop_id"
#
# DEFAULT_NAME = "Next Bus"
ICONS = {
    "Train": "mdi:train",
    "Lightrail": "mdi:tram",
    "Bus": "mdi:bus",
    "Coach": "mdi:bus",
    "Ferry": "mdi:ferry",
    "Schoolbus": "mdi:bus",
    "n/a": "mdi:clock",
    None: "mdi:clock",
}

CONF_COORDINATOR = "coordinator"
CONF_STOP_ID = "stop_id"
CONF_DESTINATION_STOP_ID = "destination_stop_id"
CONF_NUM_TRIPS = "num_trips"

CONF_ROUTE = "route"
CONF_ROUTE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_STOP_ID): cv.string,
        vol.Required(CONF_DESTINATION_STOP_ID): cv.string,
        vol.Optional(CONF_NUM_TRIPS, default=1): cv.positive_int,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Transport NSW sensor."""
    coordinator = discovery_info[CONF_COORDINATOR]
    route = discovery_info[CONF_ROUTE]

    if coordinator.data is None:
        _LOGGER.error("Initial data not available. Cannot setup sensor.")
        return

    entities = []
    for trip_index in range(route[CONF_NUM_TRIPS]):
        entities.append(
            TransportNSWTripSensor(
                coordinator,
                name=route[CONF_NAME],
                stop_id=route[CONF_STOP_ID],
                destination_stop_id=route[CONF_DESTINATION_STOP_ID],
                trip_index=trip_index,
            )
        )

    add_entities(entities)


class TransportNSWTripSensor(
    CoordinatorEntity[DataUpdateCoordinator[List[Any]]], SensorEntity
):
    _attr_attribution = "Data provided by Transport NSW"
    _attr_native_unit_of_measurement = UnitOfTime.MINUTES

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[List[Any]],
        name: str,
        stop_id: str,
        destination_stop_id: str,
        trip_index: int,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._name = name
        self._stop_id = stop_id
        self._destination_stop_id = destination_stop_id
        self._trip_index = trip_index

        self._attr_name = f"{name} {trip_index + 1}"
        self._attr_unique_id = (
            f"tnsw-{self._stop_id}-{self._destination_stop_id}-{self._trip_index}"
        )

    def _get_trip_data(self):
        if self.coordinator.data is None:
            return None

        return self.coordinator.data[self._trip_index]

    @property
    def native_value(self):
        """Return the state of the sensor."""
        data = self._get_trip_data()
        if data is None:
            return None

        return data["due"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        data = self._get_trip_data()
        if data is None:
            return None

        return {
            ATTR_DUE_IN: data["due"],
            ATTR_STOP_ID: self._stop_id,
            ATTR_ORIGIN_NAME: data["origin_name"],
            ATTR_DEPARTURE_TIME: data["departure_time"],
            ATTR_DESTINATION_STOP_ID: self._destination_stop_id,
            ATTR_DESTINATION_NAME: data["destination_name"],
            ATTR_ARRIVAL_TIME: data["arrival_time"],
            ATTR_ORIGIN_TRANSPORT_TYPE: data["origin_transport_type"],
            ATTR_ORIGIN_TRANSPORT_NAME: data["origin_transport_name"],
            ATTR_ORIGIN_LINE_NAME: data["origin_line_name"],
            ATTR_ORIGIN_LINE_NAME_SHORT: data["origin_line_name_short"],
            ATTR_CHANGES: data["changes"],
            ATTR_OCCUPANCY: data["occupancy"],
            ATTR_REAL_TIME_TRIP_ID: data["real_time_trip_id"],
            ATTR_LATITUDE: data["latitude"],
            ATTR_LONGITUDE: data["longitude"],
        }

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        data = self._get_trip_data()
        if data is None:
            return "mdi:clock"

        return ICONS[data[ATTR_ORIGIN_TRANSPORT_TYPE]]
