"""Platform for sensor integration."""
from __future__ import annotations

from typing import Any

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)

from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN
from .coordinator import WarframeStatsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

worldstate_device_name ='Warframe Worldstate Info'
worldstate_device_identifiers = (DOMAIN, 'worldstates')

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the sensor platform."""

    config = hass.data[DOMAIN][config_entry.entry_id]

    coordinator =  config['coordinator']

    sensors = []

    if config.get("worldstates"):
        if config.get("alerts"):
            sensors.append(WorldStateAlertSensor(coordinator))
        if config.get("archon_hunt"):
            sensors.append(WorldStateArchonHuntSensor(coordinator))
        # archonHunt

    async_add_entities(sensors, True)

class WorldStateAlertSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = 'Alerts'
        self._state = 0
        self._attr_extra_state_attributes = {}
        self.attrs = {}
        self._available = True
        self.entity_id = 'sensor.warframe_alerts'

        self._icon = "mdi:alert"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers = {(*worldstate_device_identifiers, self._name, self.entity_id)},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        """Handle string instances."""
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> int | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.attrs

    @property
    def native_value(self) -> int:
        return self._state

    @property
    def unique_id(self):
        """Return a unique ID."""
        return 'sensor.warframe_alerts'

    @callback
    def _handle_coordinator_update(self):
        alert_data = self.coordinator.data.get('data').get('worldstates', {}).get('alerts', {})

        alert_count = 0
        default_alert = {
            "node":"Unknown",
            "reward": {"itemString":"Unknown"},
            "type": "Unknown"
        }
        missions = []
        for alert in alert_data:
            data = {
                "node": alert.get("mission", default_alert).get("node"),
                "reward": alert.get("mission", default_alert).get("reward").get("itemString"),
                "missionType": alert.get("mission", default_alert).get("type")
            }
            missions.append(data)
            alert_count += 1
        self.attrs.update({"missions":missions})
        self._state = alert_count
        self.async_write_ha_state()

class WorldStateArchonHuntSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = 'Archon Hunt'
        self._state = None
        self.attrs = {}
        self._available = True
        self.entity_id = 'sensor.warframe_archon_hunt'

        self._icon = "mdi:calendar-week"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers = {(*worldstate_device_identifiers, self._name, self.entity_id)},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        """Handle string instances."""
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def state(self) -> int | None:
        return self._state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.attrs

    @property
    def native_value(self) -> int:
        return self._state

    @property
    def unique_id(self):
        """Return a unique ID."""
        return 'sensor.warframe_archon_hunt'

    @callback
    def _handle_coordinator_update(self):
        archon_hunt_data = self.coordinator.data.get('data').get('worldstates', {}).get('archonHunt', {})

        state = archon_hunt_data.get("boss", "Unknown")
        default_alert = {
            "node":"Unknown",
            "type": "Unknown"
        }
        missions = []
        for mission in archon_hunt_data.get("missions", [default_alert]):
            data = {
                "node": mission.get("node"),
                "missionType": mission.get("type")
            }
            missions.append(data)
        self.attrs.update({"missions":missions})
        self._state = state
        self.async_write_ha_state()