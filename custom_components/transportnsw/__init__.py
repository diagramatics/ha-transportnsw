"""The transportnsw component."""
import datetime
import logging

import voluptuous as vol
from TransportNSW import TransportNSW

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .sensor import CONF_ROUTE_SCHEMA, CONF_COORDINATOR, CONF_ROUTE, CONF_STOP_ID, CONF_DESTINATION_STOP_ID, \
    CONF_NUM_TRIPS

_LOGGER = logging.getLogger(__name__)

DOMAIN = "transportnsw"

CONF_ROUTES = 'routes'

SCAN_INTERVAL = datetime.timedelta(minutes=1)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_ROUTES): vol.All(cv.ensure_list, [
                    CONF_ROUTE_SCHEMA
                ]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    tnsw = TransportNSW()
    conf = config[DOMAIN]

    for route in conf[CONF_ROUTES]:
        async def async_update_data():
            trips = []
            wait_time = 0
            for trip_num in range(route[CONF_NUM_TRIPS]):
                trip = await hass.async_add_executor_job(
                    tnsw.get_trip, route[CONF_STOP_ID],
                    route[CONF_DESTINATION_STOP_ID], conf[CONF_API_KEY],
                    wait_time)
                trips.append(trip)
                wait_time = trip["due"] + 1

            return trips

        coordinator = DataUpdateCoordinator(
            hass,
            _LOGGER,
            name="sensor",
            update_interval=SCAN_INTERVAL,
            update_method=async_update_data,
        )
        await coordinator.async_refresh()

        hass.async_create_task(
            async_load_platform(
                hass, Platform.SENSOR, DOMAIN, {CONF_ROUTE: route, CONF_COORDINATOR: coordinator}, config
            )
        )

    return True
