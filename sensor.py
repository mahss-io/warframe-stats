"""Platform for sensor integration."""

from __future__ import annotations

from typing import Any

import logging
import datetime

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
from homeassistant.helpers.event import async_track_point_in_utc_time

import homeassistant.util.dt as dt_util
from .const import DOMAIN
from .coordinator import WarframeStatsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

worldstate_device_name = "Warframe Worldstate Info"
worldstate_device_identifiers = (DOMAIN, "worldstates")


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    config = hass.data[DOMAIN][config_entry.entry_id]

    coordinator = config["coordinator"]

    sensors = []

    if config.get("worldstates"):
        if config.get("alerts"):
            sensors.append(WorldStateAlertSensor(coordinator))
        if config.get("archon_hunt"):
            sensors.append(WorldStateArchonHuntSensor(coordinator))
        if config.get("open_worlds"):
            coordinator.data.get("data").get("worldstates", {})
            cycle_keys = []
            for key in coordinator.data.get("data").get("worldstates", {}).keys():
                if key.endswith("Cycle"):
                    cycle_keys.append(key)
            for world_key in cycle_keys:
                sensors.append(WorldStateWorldSensor(coordinator, world_key))
        if config.get("relay_events"):
            sensors.append(WorldStateRelayEventSensor(coordinator))
        if config.get("deep_archimedea"):
            sensors.append(WorldStateDeepArchimdeaSensor(coordinator))
        if config.get("events"):
            sensors.append(WorldStateEventSensor(coordinator))
        if config.get("fissures"):
            sensors.append(WorldStateFissureSensor(coordinator, "regular"))
            sensors.append(WorldStateFissureSensor(coordinator, "steel_path"))
            sensors.append(WorldStateFissureSensor(coordinator, "void_storm"))
        if config.get("invasions"):
            sensors.append(WorldStateInvasionSensor(coordinator))
        if config.get("sorties"):
            sensors.append(WorldStateSortieSensor(coordinator))
        if config.get("steel_path"):
            sensors.append(WorldStateSteelPathSensor(coordinator))
        if config.get("void_trader"):
            sensors.append(WorldStateVoidTraderSensor(coordinator))
        if config.get("varzia"):
            sensors.append(WorldStateVarziaSensor(coordinator))
        # archonHunt

    async_add_entities(sensors, True)


class WorldStateAlertSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Alerts"
        self._state = 0
        self._attr_extra_state_attributes = {}
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_alerts"

        self._icon = "mdi:alert"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
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
        return "sensor.warframe_alerts"

    @callback
    def _handle_coordinator_update(self):
        alert_data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("alerts", {})
        )

        alert_count = 0
        default_alert = {
            "node": "Unknown",
            "reward": {"itemString": "Unknown"},
            "type": "Unknown",
        }
        missions = []
        for alert in alert_data:
            data = {
                "node": alert.get("mission", default_alert).get("node"),
                "reward": alert.get("mission", default_alert)
                .get("reward")
                .get("itemString"),
                "missionType": alert.get("mission", default_alert).get("type"),
            }
            missions.append(data)
            alert_count += 1
        self.attrs.update({"missions": missions})
        self._state = alert_count
        self.async_write_ha_state()

class WorldStateArchonHuntSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Archon Hunt"
        self._state = None
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_archon_hunt"

        self._icon = "mdi:calendar-week"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
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
        return "sensor.warframe_archon_hunt"

    @callback
    def _handle_coordinator_update(self):
        archon_hunt_data = (
            self.coordinator.data.get("data")
            .get("worldstates", {})
            .get("archonHunt", {})
        )

        state = archon_hunt_data.get("boss", "Unknown")
        default_alert = {"node": "Unknown", "type": "Unknown"}
        missions = []
        for mission in archon_hunt_data.get("missions", [default_alert]):
            data = {"node": mission.get("node"), "missionType": mission.get("type")}
            missions.append(data)
        self.attrs.update({"missions": missions})
        self._state = state
        self.async_write_ha_state()

class WorldStateWorldSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, world_key):
        super().__init__(coordinator, world_key)
        self.world_name = world_key.replace("Cycle", "")
        self.world_key = world_key
        self._name = self.world_name.capitalize() + " Cycle"
        self._state = None
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_" + self.world_name + "_cycle"

        self._icon = "mdi:earth"

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
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
        return "sensor.warframe_" + self.world_name + "_cycle"

    @callback
    def async_update_at_time(self, now: datetime.datetime) -> None:
        expiry = self.attrs.get("expiry", dt_util.utcnow())
        states = []
        target_index = 0
        match self.world_name:
            case "earth":
                states = ["day", "night"]
            case "cetus":
                states = ["day", "night"]
            case "cambion":
                states = ["fass", "vome"]
            case "zariman":
                states = ["grineer", "courpus"]
            case "vallis":
                states = ["warm", "cold"]
            case "duviri":
                states = ["joy", "anger", "envy", "sorrow", "fear"]
        index_of = states.index(self._state)
        if index_of < (len(states)-1):
            target_index = index_of + 1
        self.attrs.update({"expiry": None})
        self._state = states[target_index]
        if len(states) != 0:
            self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self):
        world_state_data = (
            self.coordinator.data.get("data")
            .get("worldstates", {})
            .get(self.world_key, {})
        )

        expiry = dt_util.parse_datetime(world_state_data.get("expiry", "2000-01-01T00:00:00.000Z"))
        if expiry < (dt_util.utcnow() + datetime.timedelta(hours=1)):
            async_track_point_in_utc_time(
                self.hass, self.async_update_at_time, expiry
            )
        self.attrs.update({"expiry": expiry})
        self._state = world_state_data.get("state")
        self.async_write_ha_state()

class WorldStateRelayEventSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Relay Events"
        self._state = "None"
        self._attr_extra_state_attributes = {}
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_relay_events"

        self._icon = "mdi:calendar-alert"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_relay_events"

    @callback
    def _handle_coordinator_update(self):
        relay_event_data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("constructionProgress", {})
        )

        fomorian = float(relay_event_data.get("fomorianProgress", "0"))
        razorback = float(relay_event_data.get("razorbackProgress", "0"))

        self.attrs.update({"fomorian": fomorian,"razorback":razorback})
        self._state = "Ongoing" if fomorian >= 100 or razorback >= 100 else "None"
        self.async_write_ha_state()

class WorldStateDeepArchimdeaSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Deep Archimdea"
        self._state = "None"
        self._attr_extra_state_attributes = {}
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_deep_archimdea"

        self._icon = "mdi:bolt"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_deep_archimdea"

    @callback
    def _handle_coordinator_update(self):
        deep_archimdea_data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("deepArchimedea", {})
        )

        missions_data = deep_archimdea_data.get("missions", {})
        state = ""
        index = 0
        for mission in missions_data:
            mission_name =  mission.get("mission", "Unknown")
            state += mission_name
            if index < len(missions_data)-1:
                state += " - "
            index += 1

        personalModifiers = []
        personalModifiers_data = deep_archimdea_data.get("personalModifiers", {})
        for modifier in personalModifiers_data:
            data = {"name":modifier.get("name"),"description":modifier.get("description")}
            personalModifiers.append(data)
        self.attrs.update({"personalModifiers": personalModifiers})
        self._state = state
        self.async_write_ha_state()

class WorldStateEventSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Events"
        self._state = 0
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_events"

        self._icon = "mdi:calendar-star"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_events"

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("events", {})
        )

        event_count = 0
        event_data = {}
        for event in _data:
            event_count += 1
            event_data.update({"name": event.get("description")})


        self.attrs = event_data
        self._state = event_count
        self.async_write_ha_state()

class WorldStateFissureSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, fissure_type):
        super().__init__(coordinator)

        self.fissure_type = fissure_type
        self._name = fissure_type.capitalize().replace("_", " ") + " Fissures"
        self._state = 0
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_"+ fissure_type + "_fissures"

        self._icon = "mdi:ballot-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_"+ self.fissure_type + "_fissures"

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("fissures", {})
        )

        count = 0
        data = []
        for fissure in _data:
            if fissure.get("expired") == False:
                if fissure.get("isStorm") == True and self.fissure_type == "void_storm":
                    count += 1
                    data.append({
                        "node": fissure.get("node"),
                        "missionType": fissure.get("missionType"),
                        "enemy": fissure.get("enemy"),
                        "tier": fissure.get("tier")
                    })
                elif fissure.get("isHard") == True and self.fissure_type == "steel_path":
                    count += 1
                    data.append({
                        "node": fissure.get("node"),
                        "missionType": fissure.get("missionType"),
                        "enemy": fissure.get("enemy"),
                        "tier": fissure.get("tier")
                    })
                elif self.fissure_type == "regular":
                    count += 1
                    data.append({
                        "node": fissure.get("node"),
                        "missionType": fissure.get("missionType"),
                        "enemy": fissure.get("enemy"),
                        "tier": fissure.get("tier")
                    })
        self.attrs.update({"fissures":data})
        self._state = count
        self.async_write_ha_state()

class WorldStateInvasionSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Invasions"
        self._state = 0
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_invasions"

        self._icon = "mdi:ammunition"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_invasions"

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("invasions", {})
        )

        count = 0
        data = []
        for invasion in _data:
            if invasion.get("completed") != False:
                count += 1
                data.append({
                    "node": invasion.get("node"),
                    "rewardTypes": invasion.get("rewardTypes"),
                    "enemy": invasion.get("defender").get("faction")
                })
        self.attrs.update({"invasions":data})
        self._state = count
        self.async_write_ha_state()

class WorldStateSortieSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Sorties"
        self._state = ""
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_"

        self._icon = "mdi:calendar-today"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_"

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("sortie", {})
        )

        missions = _data.get("variants", {})

        missions_data = []
        state = ""
        index = 0
        for mission in missions:
            mission_name =  mission.get("missionType", "Unknown")
            missions_data.append({
                "node": mission.get("node"),
                "missionType": mission_name,
                "modifier": mission.get("modifier")
            })
            state += mission_name
            if index < len(missions)-1:
                state += " - "
            index += 1

        self.attrs.update({"missions": missions_data})
        self._state = state
        self.async_write_ha_state()

class WorldStateSteelPathSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Steel Path Honor"
        self._state = ""
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_steel_path_teshin"

        self._icon = "mdi:calendar-week"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_steel_path_teshin"

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("steelPath", {})
        )

        self._state = _data.get("currentReward", {}).get("name")
        self.async_write_ha_state()

class WorldStateVoidTraderSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Void Trader"
        self._state = "Inactive "
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_void_trader"

        self._icon = "mdi:storefront-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_void_trader"

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("voidTrader", {})
        )

        if _data.get("active"):
            self._state = "Active"
            self.attrs.update({"inventory": _data.get("inventory")})
        else:
            self._state = "Inactive"
            self.attrs.update({"inventory": []})
        self.async_write_ha_state()

class WorldStateVarziaSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._name = "Primed Resurgence"
        self._state = 0
        self.attrs = {}
        self._available = True
        self.entity_id = "sensor.warframe_prime_resurgence_rotation"

        self._icon = "mdi:storefront-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={worldstate_device_identifiers},
            name=worldstate_device_name,
        )

    @property
    def icon(self):
        return self._icon

    @property
    def state_class(self) -> SensorStateClass:
        return SensorStateClass.MEASUREMENT

    @property
    def name(self) -> str:
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
        return "sensor.warframe_prime_resurgence_rotation"

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("data").get("worldstates", {}).get("vaultTrader", {})
        )

        count = 0
        data = []

        inventory = _data.get("inventory",[])
        for item in inventory:
            data.append({
                "name": item.get("item"),
                "aya": item.get("credits"),
                "regal_aya": item.get("ducats")
            })
            count += 1

        self.attrs.update({"items":data})
        self._state = count
        self.async_write_ha_state()
