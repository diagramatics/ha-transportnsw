"""Support for Transport NSW (AU) to query next leave event."""
from __future__ import annotations
import logging

from datetime import timedelta

from TransportNSW import TransportNSW
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import ATTR_MODE, CONF_API_KEY, CONF_NAME, UnitOfTime
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

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

CONF_STOP_ID = "stop_id"
CONF_DESTINATION_STOP_ID = "destination_stop_id"

DEFAULT_NAME = "Next Bus"
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

SCAN_INTERVAL = timedelta(seconds=60)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_STOP_ID): cv.string,
        vol.Required(CONF_DESTINATION_STOP_ID): cv.string,
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Transport NSW sensor."""
    stop_id = config[CONF_STOP_ID]
    api_key = config[CONF_API_KEY]
    destination_stop_id = config.get(CONF_DESTINATION_STOP_ID)
    name = config.get(CONF_NAME)

    _LOGGER.debug("Setup %s %s %s", stop_id, name, destination_stop_id)

    data = PublicTransportData(stop_id, destination_stop_id, api_key)
    add_entities([TransportNSWSensor(data, stop_id, name)], False)


class TransportNSWSensor(SensorEntity):
    """Implementation of an Transport NSW sensor."""

    _attr_attribution = "Data provided by Transport NSW"

    def __init__(self, data, stop_id, name):
        """Initialize the sensor."""
        self.data = data
        self._name = name
        self._stop_id = stop_id
        self._times = self._state = None
        self._icon = ICONS[None]
        _LOGGER.debug("%s %s %s", self._name, self._stop_id, self._icon)

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self._times is not None:
            return {
                ATTR_DUE_IN: self._times[ATTR_DUE_IN],
                ATTR_STOP_ID: self._stop_id,
                ATTR_ORIGIN_NAME: self._times[ATTR_ORIGIN_NAME],
                ATTR_DEPARTURE_TIME: self._times[ATTR_DEPARTURE_TIME],
                ATTR_DESTINATION_STOP_ID: self._times[ATTR_DESTINATION_STOP_ID],
                ATTR_DESTINATION_NAME: self._times[ATTR_DESTINATION_NAME],
                ATTR_ARRIVAL_TIME: self._times[ATTR_ARRIVAL_TIME],
                ATTR_ORIGIN_TRANSPORT_TYPE: self._times[ATTR_ORIGIN_TRANSPORT_TYPE],
                ATTR_ORIGIN_TRANSPORT_NAME: self._times[ATTR_ORIGIN_TRANSPORT_NAME],
                ATTR_ORIGIN_LINE_NAME: self._times[ATTR_ORIGIN_LINE_NAME],
                ATTR_ORIGIN_LINE_NAME_SHORT: self._times[ATTR_ORIGIN_LINE_NAME_SHORT],
                ATTR_CHANGES: self._times[ATTR_CHANGES],
                ATTR_OCCUPANCY: self._times[ATTR_OCCUPANCY],
                ATTR_REAL_TIME_TRIP_ID: self._times[ATTR_REAL_TIME_TRIP_ID],
                ATTR_LATITUDE: self._times[ATTR_LATITUDE],
                ATTR_LONGITUDE: self._times[ATTR_LONGITUDE],
            }

    @property
    def native_unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return UnitOfTime.MINUTES

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    def update(self) -> None:
        """Get the latest data from Transport NSW and update the states."""
        self.data.update()
        self._times = self.data.info
        self._state = self._times[ATTR_DUE_IN]
        self._icon = ICONS[self._times[ATTR_ORIGIN_TRANSPORT_TYPE]]

        _LOGGER.debug("Update: %s %s %s", self._icon, self._times[ATTR_DUE_IN], self._times[ATTR_DESTINATION_STOP_ID])


class PublicTransportData:
    """The Class for handling the data retrieval."""

    def __init__(self, stop_id, destination, api_key):
        """Initialize the data object."""
        self._stop_id = stop_id
        self._destination = destination
        self._api_key = api_key
        self.info = {
            ATTR_DUE_IN: "n/a",
            ATTR_STOP_ID: self._stop_id,
            ATTR_ORIGIN_NAME: "n/a",
            ATTR_DEPARTURE_TIME: "n/a",
            ATTR_DESTINATION_STOP_ID: self._destination,
            ATTR_DESTINATION_NAME: "n/a",
            ATTR_ARRIVAL_TIME: "n/a",
            ATTR_ORIGIN_TRANSPORT_TYPE: "n/a",
            ATTR_ORIGIN_TRANSPORT_NAME: "n/a",
            ATTR_ORIGIN_LINE_NAME: "n/a",
            ATTR_ORIGIN_LINE_NAME_SHORT: "n/a",
            ATTR_CHANGES: "n/a",
            ATTR_OCCUPANCY: "n/a",
            ATTR_REAL_TIME_TRIP_ID: "n/a",
            ATTR_LATITUDE: "n/a",
            ATTR_LONGITUDE: "n/a",
        }
        self.tnsw = TransportNSW()

    def update(self):
        """Get the next leave time."""
        _data = self.tnsw.get_trip(
            self._stop_id, self._destination, self._api_key
        )
        self.info = {
            ATTR_DUE_IN: _data["due"],
            ATTR_STOP_ID: self._stop_id,
            ATTR_ORIGIN_NAME: _data["origin_name"],
            ATTR_DEPARTURE_TIME: _data["departure_time"],
            ATTR_DESTINATION_STOP_ID: self._destination,
            ATTR_DESTINATION_NAME: _data["destination_name"],
            ATTR_ARRIVAL_TIME: _data["arrival_time"],
            ATTR_ORIGIN_TRANSPORT_TYPE: _data["origin_transport_type"],
            ATTR_ORIGIN_TRANSPORT_NAME: _data["origin_transport_name"],
            ATTR_ORIGIN_LINE_NAME: _data["origin_line_name"],
            ATTR_ORIGIN_LINE_NAME_SHORT: _data["origin_line_name_short"],
            ATTR_CHANGES: _data["changes"],
            ATTR_OCCUPANCY: _data["occupancy"],
            ATTR_REAL_TIME_TRIP_ID: _data["real_time_trip_id"],
            ATTR_LATITUDE: _data["latitude"],
            ATTR_LONGITUDE: _data["longitude"],
        }
