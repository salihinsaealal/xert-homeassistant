"""The Xert integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import DOMAIN, UPDATE_INTERVAL
from .coordinator import XertDataUpdateCoordinator
from .version import __version__

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

# Service schemas
SERVICE_REFRESH_DATA = "refresh_data"
SERVICE_DOWNLOAD_WORKOUT = "download_workout"

REFRESH_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional("entry_id"): cv.string,
    }
)

DOWNLOAD_WORKOUT_SCHEMA = vol.Schema(
    {
        vol.Required("workout_id"): cv.string,
        vol.Optional("format", default="zwo"): vol.In(["zwo", "erg"]),
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Xert from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)
    coordinator = XertDataUpdateCoordinator(
        hass,
        session,
        entry,
        UPDATE_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Create device for this integration
    _create_device(hass, entry, coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services on first setup
    if not hass.services.has_service(DOMAIN, SERVICE_REFRESH_DATA):
        async def handle_refresh_data(call: ServiceCall) -> None:
            """Handle refresh data service call."""
            entry_id = call.data.get("entry_id")
            
            if entry_id:
                # Refresh specific entry
                if entry_id in hass.data[DOMAIN]:
                    await hass.data[DOMAIN][entry_id].async_request_refresh()
                    _LOGGER.info("Refreshed data for entry %s", entry_id)
                else:
                    _LOGGER.error("Entry ID %s not found", entry_id)
            else:
                # Refresh all entries
                for coordinator in hass.data[DOMAIN].values():
                    await coordinator.async_request_refresh()
                _LOGGER.info("Refreshed data for all Xert integrations")

        hass.services.async_register(
            DOMAIN,
            SERVICE_REFRESH_DATA,
            handle_refresh_data,
            schema=REFRESH_DATA_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_DOWNLOAD_WORKOUT):
        async def handle_download_workout(call: ServiceCall) -> None:
            """Handle download workout service call."""
            workout_id = call.data["workout_id"]
            format_type = call.data.get("format", "zwo")
            
            # Get the first coordinator (assuming single account)
            coordinators = list(hass.data[DOMAIN].values())
            if not coordinators:
                _LOGGER.error("No Xert integration configured")
                return
            
            coordinator = coordinators[0]
            
            try:
                workout_data = await coordinator.download_workout(workout_id, format_type)
                _LOGGER.info(
                    "Downloaded workout %s in %s format (%d bytes)",
                    workout_id,
                    format_type,
                    len(workout_data),
                )
                # You can save to file or return data as needed
                # For now, just log success
            except Exception as err:
                _LOGGER.error("Failed to download workout: %s", err)

        hass.services.async_register(
            DOMAIN,
            SERVICE_DOWNLOAD_WORKOUT,
            handle_download_workout,
            schema=DOWNLOAD_WORKOUT_SCHEMA,
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _create_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: XertDataUpdateCoordinator,
) -> None:
    """Create a device for the Xert integration."""
    device_registry = async_get_device_registry(hass)
    
    username = entry.data.get("username", "Xert Online")
    
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=f"Xert Online - {username}",
        manufacturer="Xert Online",
        model="API Client",
        sw_version=__version__,
        hw_version="1.0",
        configuration_url="https://www.xertonline.com/",
    )