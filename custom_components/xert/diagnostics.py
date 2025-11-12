"""Diagnostics support for Xert integration."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Redact sensitive information
    config_data = {
        "username": entry.data.get("username", "REDACTED"),
        "access_token": "REDACTED" if coordinator._access_token else None,
        "refresh_token": "REDACTED" if coordinator._refresh_token else None,
        "token_expires_at": (
            coordinator._token_expires.isoformat()
            if coordinator._token_expires
            else None
        ),
    }
    
    # Include coordinator state
    coordinator_info = {
        "last_update_success": coordinator.last_update_success,
        "last_update_time": (
            coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None
        ),
        "update_interval": str(coordinator.update_interval),
        "is_refreshing": coordinator._is_refreshing,
    }
    
    # Include current data (non-sensitive)
    current_data = {}
    if coordinator.data:
        current_data = {
            "fitness_status": coordinator.data.get("fitness_status", {}),
            "training_progress": {
                "state": coordinator.data.get("training_progress", {}).get("state"),
                "has_attributes": bool(
                    coordinator.data.get("training_progress", {}).get("attributes")
                ),
            },
            "workout_manager": coordinator.data.get("workout_manager", {}),
            "recent_activity": {
                "state": coordinator.data.get("recent_activity", {}).get("state"),
                "has_attributes": bool(
                    coordinator.data.get("recent_activity", {}).get("attributes")
                ),
            },
            "token_status": coordinator.data.get("token_status", {}),
            "wotd": coordinator.data.get("wotd", {}),
        }
    
    return {
        "config": config_data,
        "coordinator": coordinator_info,
        "data": current_data,
    }
