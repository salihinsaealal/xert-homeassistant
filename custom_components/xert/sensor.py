"""Sensor platform for Xert integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    DOMAIN,
    SENSOR_FITNESS_STATUS,
    SENSOR_TRAINING_PROGRESS,
    SENSOR_WORKOUT_MANAGER,
    SENSOR_RECENT_ACTIVITY,
    SENSOR_TOKEN_STATUS,
    SENSOR_WOTD,
)
from .coordinator import XertDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Xert sensor based on a config entry."""
    coordinator: XertDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [
            XertFitnessStatusSensor(coordinator),
            XertTrainingProgressSensor(coordinator),
            XertWorkoutManagerSensor(coordinator),
            XertRecentActivitySensor(coordinator),
            XertTokenStatusSensor(coordinator),
            XertWOTDSensor(coordinator),
        ]
    )


class XertSensor(SensorEntity):
    """Base class for Xert sensors."""

    def __init__(self, coordinator: XertDataUpdateCoordinator, sensor_type: str) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self._sensor_type = sensor_type
        self._attr_has_entity_name = True

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )


class XertFitnessStatusSensor(XertSensor):
    """Representation of Xert Fitness Status sensor."""

    def __init__(self, coordinator: XertDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, SENSOR_FITNESS_STATUS)
        username = self.coordinator.config_data.get("username", "xert")
        self._attr_name = f"{username}_fitness_status"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{SENSOR_FITNESS_STATUS}"

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        data = self.coordinator.data.get("fitness_status", {})
        return data.get("state", "Unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        data = self.coordinator.data.get("fitness_status", {})
        return data.get("attributes", {})


class XertTrainingProgressSensor(XertSensor):
    """Representation of Xert Training Progress sensor."""

    def __init__(self, coordinator: XertDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, SENSOR_TRAINING_PROGRESS)
        username = self.coordinator.config_data.get("username", "xert")
        self._attr_name = f"{username}_training_progress"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{SENSOR_TRAINING_PROGRESS}"

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        data = self.coordinator.data.get("training_progress", {})
        return data.get("state", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        data = self.coordinator.data.get("training_progress", {})
        return data.get("attributes", {})


class XertWorkoutManagerSensor(XertSensor):
    """Representation of Xert Workout Manager sensor."""

    def __init__(self, coordinator: XertDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, SENSOR_WORKOUT_MANAGER)
        username = self.coordinator.config_data.get("username", "xert")
        self._attr_name = f"{username}_workout_manager"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{SENSOR_WORKOUT_MANAGER}"

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        data = self.coordinator.data.get("workout_manager", {})
        return data.get("state", 0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        data = self.coordinator.data.get("workout_manager", {})
        return data.get("attributes", {})


class XertRecentActivitySensor(XertSensor):
    """Representation of Xert Recent Activity sensor."""

    def __init__(self, coordinator: XertDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, SENSOR_RECENT_ACTIVITY)
        username = self.coordinator.config_data.get("username", "xert")
        self._attr_name = f"{username}_recent_activity"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{SENSOR_RECENT_ACTIVITY}"

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        data = self.coordinator.data.get("recent_activity", {})
        return data.get("state", "No recent activity")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        data = self.coordinator.data.get("recent_activity", {})
        return data.get("attributes", {})


class XertTokenStatusSensor(XertSensor):
    """Representation of Xert Token Status sensor."""

    def __init__(self, coordinator: XertDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, SENSOR_TOKEN_STATUS)
        username = self.coordinator.config_data.get("username", "xert")
        self._attr_name = f"{username}_token_status"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{SENSOR_TOKEN_STATUS}"

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        data = self.coordinator.data.get("token_status", {})
        return data.get("state", "Unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes."""
        data = self.coordinator.data.get("token_status", {})
        return data.get("attributes", {})


class XertWOTDSensor(XertSensor):
    """Representation of Xert Workout of the Day sensor."""

    def __init__(self, coordinator: XertDataUpdateCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, SENSOR_WOTD)
        username = self.coordinator.config_data.get("username", "xert")
        self._attr_name = f"{username}_wotd"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{SENSOR_WOTD}"

    @property
    def state(self) -> StateType:
        """Return the state of the sensor (WOTD name)."""
        data = self.coordinator.data.get("wotd", {})
        return data.get("state", None)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return entity specific state attributes for WOTD."""
        data = self.coordinator.data.get("wotd", {})
        return data.get("attributes", {}) 