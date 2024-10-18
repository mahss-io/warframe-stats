"""Platform for sensor integration."""

from __future__ import annotations

from typing import Any

import logging
import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    RestoreSensor,
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
from .coordinator import (
    WarframeStaticDataUpdateCoordinator,
    WarframeWorldstateDataUpdateCoordinator,
    WarframeProfileDataUpdateCoordinator
)

_LOGGER = logging.getLogger(__name__)

worldstate_device = DeviceInfo(
            identifiers={(DOMAIN, "worldstates")},
            name="Warframe Worldstate Info",
        )

profile_device_base_identifiers=(DOMAIN, "profile")
profile_device_base_name="Warframe "

most_used_types = [
    "warframe",
    "primary",
    "secondary",
    "melee",
    "companion"
]

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""

    config = hass.data[DOMAIN][config_entry.entry_id]

    staticDataCoordinator = config["coordinator"][0]
    worldstateCoordinator = config["coordinator"][1]
    profileCoordinator = config["coordinator"][2]

    sensors = []

    if config.get("worldstates"):
        sensors.append(WorldStateLastUpdateSensor(worldstateCoordinator, staticDataCoordinator))
        if config.get("alerts"):
            sensors.append(WorldStateAlertSensor(worldstateCoordinator))
        if config.get("archon_hunt"):
            sensors.append(WorldStateArchonHuntSensor(worldstateCoordinator))
        if config.get("open_worlds"):
            cycle_keys = []
            for key in worldstateCoordinator.data.keys():
                if key.endswith("Cycle"):
                    cycle_keys.append(key)
            for world_key in cycle_keys:
                sensors.append(WorldStateWorldSensor(worldstateCoordinator, world_key))
        if config.get("relay_events"):
            sensors.append(WorldStateRelayEventSensor(worldstateCoordinator))
        if config.get("deep_archimedea"):
            sensors.append(WorldStateDeepArchimdeaSensor(worldstateCoordinator))
        if config.get("events"):
            sensors.append(WorldStateEventSensor(worldstateCoordinator))
        if config.get("fissures"):
            sensors.append(WorldStateFissureSensor(worldstateCoordinator, "regular"))
            sensors.append(WorldStateFissureSensor(worldstateCoordinator, "steel_path"))
            sensors.append(WorldStateFissureSensor(worldstateCoordinator, "void_storm"))
        if config.get("invasions"):
            sensors.append(WorldStateInvasionSensor(worldstateCoordinator))
        if config.get("sorties"):
            sensors.append(WorldStateSortieSensor(worldstateCoordinator))
        if config.get("steel_path"):
            sensors.append(WorldStateSteelPathSensor(worldstateCoordinator))
        if config.get("void_trader"):
            sensors.append(WorldStateVoidTraderSensor(worldstateCoordinator))
        if config.get("varzia"):
            sensors.append(WorldStateVarziaSensor(worldstateCoordinator))
    if config.get("profiles"):
        for username in config.get("usernames"):
            if config.get("total_abilities_used"):
                sensors.append(ProfileAbilitiesSensor(profileCoordinator, username, staticDataCoordinator))
            if config.get("total_enemies_killed"):
                sensors.append(ProfileEnemiesSensor(profileCoordinator, username, staticDataCoordinator))
            if config.get("most_scans"):
                sensors.append(ProfileScansSensor(profileCoordinator, username, staticDataCoordinator))
            if config.get("credits"):
                sensors.append(ProfileCreditSensor(profileCoordinator, username))
            if config.get("rank"):
                sensors.append(ProfileRankSensor(profileCoordinator, username))
            if config.get("death"):
                sensors.append(ProfileDeathSensor(profileCoordinator, username, staticDataCoordinator))
            if config.get("time_played"):
                sensors.append(ProfileTimePlayedSensor(profileCoordinator, username))
            if config.get("star_chart_completion"):
                sensors.append(ProfileStarChartSensor(profileCoordinator, username, staticDataCoordinator))
            # for type in most_used_types:
            #     if config.get("most_used_warframe") and type == "warframe":
            #         sensors.append(ProfileMostUsedSensor(coordinator, username, type))
            #     if config.get("most_used_primary") and type == "primary":
            #         sensors.append(ProfileMostUsedSensor(coordinator, username, type))
            #     if config.get("most_used_secondary") and type == "secondary":
            #         sensors.append(ProfileMostUsedSensor(coordinator, username, type))
            #     if config.get("most_used_melee") and type == "melee":
            #         sensors.append(ProfileMostUsedSensor(coordinator, username, type))
            #     if config.get("most_used_companion") and type == "companion":
            #         sensors.append(ProfileMostUsedSensor(coordinator, username, type))

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
        return worldstate_device

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
            self.coordinator.data.get("alerts", {})
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
        return worldstate_device

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
            self.coordinator.data
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
        return worldstate_device

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

    # @callback
    # def async_update_at_time(self, now: datetime.datetime) -> None:
    #     expiry = self.attrs.get("expiry", dt_util.utcnow())
    #     states = []
    #     target_index = 0
    #     match self.world_name:
    #         case "earth":
    #             states = ["day", "night"]
    #         case "cetus":
    #             states = ["day", "night"]
    #         case "cambion":
    #             states = ["fass", "vome"]
    #         case "zariman":
    #             states = ["grineer", "courpus"]
    #         case "vallis":
    #             states = ["warm", "cold"]
    #         case "duviri":
    #             states = ["joy", "anger", "envy", "sorrow", "fear"]
    #     index_of = states.index(self._state)
    #     if index_of < (len(states)-1):
    #         target_index = index_of + 1
    #     self.attrs.update({"expiry": None})
    #     self._state = states[target_index]
    #     if len(states) != 0:
    #         self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self):
        world_state_data = (
            self.coordinator.data
            .get(self.world_key, {})
        )

        expiry = dt_util.parse_datetime(world_state_data.get("expiry", "2000-01-01T00:00:00.000Z"))
        # if expiry < (dt_util.utcnow() + datetime.timedelta(hours=1)):
        #     async_track_point_in_utc_time(
        #         self.hass, self.async_update_at_time, expiry
        #     )
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
        return worldstate_device

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
            self.coordinator.data.get("constructionProgress", {})
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
        return worldstate_device

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
            self.coordinator.data.get("deepArchimedea", {})
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
        return worldstate_device

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
            self.coordinator.data.get("events", {})
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
        return worldstate_device

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
            self.coordinator.data.get("fissures", {})
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
        return worldstate_device

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
            self.coordinator.data.get("invasions", {})
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
        return worldstate_device

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
            self.coordinator.data.get("sortie", {})
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
        return worldstate_device

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
            self.coordinator.data.get("steelPath", {})
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
        return worldstate_device

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
            self.coordinator.data.get("voidTrader", {})
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
        return worldstate_device

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
            self.coordinator.data.get("vaultTrader", {})
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

class WorldStateLastUpdateSensor(CoordinatorEntity, RestoreSensor, SensorEntity):
    _attr_icon = "mdi:mdi-newspaper"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, staticDataCoordinator):
        super().__init__(coordinator)

        self.static_data = staticDataCoordinator
        self._attr_name = "Last Update"
        self._attr_unique_id = "sensor.warframe_last_update"
        self._attr_device_info = worldstate_device

    async def async_added_to_hass(self) -> None:
        """Handle entity which will be added."""
        if state := await self.async_get_last_state():
            self._attr_native_value = state.state
        await super().async_added_to_hass()

    @callback
    def _handle_coordinator_update(self):
        news_data = (
            self.coordinator.data.get("news", [])
        )

        newest_news = ""
        newest_news_date = dt_util.parse_datetime("2000-01-01T01:01:00.000Z")

        for news in news_data:
            if news.get("update"):
                date = dt_util.parse_datetime(news.get("date", "2000-01-01T01:01:00.000Z"))
                if newest_news_date < date:
                    newest_news_date = date
                    newest_news = news.get("message")

        self._attr_native_value = newest_news
        self.async_write_ha_state()


class ProfileAbilitiesSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:exclamation-thick"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator)

        self.username = username
        self.static_data = staticDataCoordinator
        self._attr_name = username + " Abilities Used"
        self._attr_unique_id = f"sensor.warframe_{username}_abilities_used"
        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @callback
    def _handle_coordinator_update(self):
        user_ability_data = (
            self.coordinator.data.get(self.username, {}).get("abilities", [])
        )

        ability_count = 0
        abilities_used = []
        for ability in user_ability_data:
            key = ability.get("uniqueName")
            used = int(ability.get("used", 0))
            ability_name = _get_partial_lookup(key, self.static_data.name_lookup)
            ability_count += used
            abilities_used.append({
                "name": ability_name.get("value") if isinstance(ability_name, dict) else key,
                "used": used
            })

        self._attr_extra_state_attributes.update({"abilities": abilities_used})
        self._attr_native_value = ability_count
        self.async_write_ha_state()

class ProfileEnemiesSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:ammunition"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator)

        self.username = username
        self.static_data = staticDataCoordinator
        self._attr_name = username + " Enemies Killed"
        self._attr_unique_id = f"sensor.warframe_{username}_enemies_killed"
        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @callback
    def _handle_coordinator_update(self):
        user_enemie_data = (
            self.coordinator.data.get(self.username, {}).get("enemies", [])
        )

        enemies_killed_count = 0
        enemies_killed = []
        for enemy in user_enemie_data:
            key = enemy.get("uniqueName")
            killed = int(enemy.get("kills", 0))
            enemy_name = _get_partial_lookup(key, self.static_data.name_lookup)
            enemies_killed_count += killed
            enemies_killed.append({
                "name": enemy_name.get("value") if isinstance(enemy_name, dict) else key,
                "killed": killed
            })

        self._attr_extra_state_attributes.update({"enemies_killed": enemies_killed})
        self._attr_native_value = enemies_killed_count
        self.async_write_ha_state()

class ProfileScansSensor(CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:skull-scan-outline"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator)

        self.username = username
        self.static_data = staticDataCoordinator
        self._attr_name = username + " Most Scans"
        self._attr_unique_id = f"sensor.warframe_{username}_most_scans"
        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @callback
    def _handle_coordinator_update(self):
        user_enemie_data = (
            self.coordinator.data.get(self.username, {}).get("scans", [])
        )

        max_scan_amount = 0
        max_scan_item = ""
        items_scanned = []
        for enemy in user_enemie_data:
            key = enemy.get("uniqueName")
            scans = int(enemy.get("scans", 0))
            item_name = _get_partial_lookup(key, self.static_data.name_lookup)
            if max_scan_amount < scans:
                max_scan_amount = scans
                max_scan_item = item_name.get("value") if isinstance(item_name, dict) else key

            items_scanned.append({
                "name": item_name.get("value") if isinstance(item_name, dict) else key,
                "scans": scans
            })

        self._attr_extra_state_attributes.update({"max_scanned": {"name":max_scan_item, "scans": max_scan_amount}, "items_scanned": items_scanned})
        self._attr_native_value = max_scan_item
        self.async_write_ha_state()

class ProfileCreditSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:micro-sd"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, username):
        super().__init__(coordinator)

        self.username = username
        self._attr_name = username + " Total Credits"
        self._attr_unique_id = f"sensor.warframe_{username}_total_credits"
        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @callback
    def _handle_coordinator_update(self):
        credit_data = (
            self.coordinator.data.get(self.username, {}).get("income", 0)
        )
        time_played_seconds_data = (
            self.coordinator.data.get(self.username, {}).get("timePlayedSec", 0)
        )

        self._attr_extra_state_attributes.update({"credits_per_hour": credit_data/((time_played_seconds_data/60)/60)})
        self._attr_native_value = credit_data
        self.async_write_ha_state()

class ProfileRankSensor(CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:chevron-triple-up"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, username):
        super().__init__(coordinator)

        self.username = username
        self._attr_name = username + " Rank"
        self._attr_unique_id = f"sensor.warframe_{username}_rank"
        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @callback
    def _handle_coordinator_update(self):
        rank_data = (
            self.coordinator.data.get(self.username, {}).get("playerLevel", 0)
        )

        rank = 0
        is_legendary = False
        if rank_data > 30:
            is_legendary = True
            rank = rank_data - 30
        time_played_seconds_data = (
            self.coordinator.data.get(self.username, {}).get("timePlayedSec", 0)
        )

        self._attr_extra_state_attributes.update({"rank_per_day": rank_data/(((time_played_seconds_data/60)/60)/24)})
        self._attr_native_value = ("Legendary " if is_legendary else "") + str(rank)
        self.async_write_ha_state()

class ProfileDeathSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:robot-dead-outline"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator)

        self.username = username
        self.static_data = staticDataCoordinator
        self._attr_name = username + " Deaths"
        self._attr_unique_id = f"sensor.warframe_{username}_deaths"
        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @callback
    def _handle_coordinator_update(self):
        death_data = (
            self.coordinator.data.get(self.username, {}).get("deaths", 0)
        )
        user_enemy_data = (
            self.coordinator.data.get(self.username, {}).get("enemies", [])
        )

        enemies_that_killed_player = []
        for enemy in user_enemy_data:
            if enemy.get("deaths"):
                key = enemy.get("uniqueName")
                deaths = int(enemy.get("deaths", 0))
                enemy_name = _get_partial_lookup(key, self.static_data.name_lookup)
                enemies_that_killed_player.append({
                    "name": enemy_name.get("value") if isinstance(enemy_name, dict) else key,
                    "deaths": deaths
                })

        self._attr_extra_state_attributes.update({"player_kills": enemies_that_killed_player})
        self._attr_native_value = death_data
        self.async_write_ha_state()

class ProfileTimePlayedSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-alert-outline"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, username):
        super().__init__(coordinator)

        self.username = username
        self._attr_name = username + " Time Played"
        self._attr_unique_id = f"sensor.warframe_{username}_time_played"
        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @callback
    def _handle_coordinator_update(self):
        time_played_data = (
            self.coordinator.data.get(self.username, {}).get("timePlayedSec", 0)
        )
        seconds_played = float(time_played_data)
        minutes_played = seconds_played/60.0
        hours_played = minutes_played/60.0
        days_played = hours_played/24.0
        months_played = days_played/30.44

        self._attr_extra_state_attributes.update({
            "seconds_played": time_played_data,
            "minutes_played": seconds_played,
            "hours_played": hours_played,
            "days_played": days_played,
            "months_played": months_played,
            })
        self._attr_native_value = hours_played
        self.async_write_ha_state()

class ProfileStarChartSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:map-marker-path"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator)

        self.username = username
        self.static_data = staticDataCoordinator
        self._attr_name = username + " Star Chart Completion"
        self._attr_unique_id = f"sensor.warframe_{username}_star_chart_completion"
        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, self.username)},
            name=profile_device_base_name + self.username
        )

    @callback
    def _handle_coordinator_update(self):
        mission_data = (
            self.coordinator.data.get(self.username, {}).get("missions", [])
        )

        total_missions = 0
        total_completed_missions = 0
        steel_path = []
        regular = []
        for mission in mission_data:
            nodeKey = mission.get("nodeKey")
            complete = True if mission.get("highScore") else False
            nodeName = _get_partial_lookup(nodeKey, self.static_data.name_lookup)
            if nodeName:
                total_missions += 1
                if complete:
                    total_completed_missions += 1
                    highScore = mission.get("highScore", 0)
                    if _check_hard_mode(nodeKey):
                        steel_path.append({
                            "node": nodeName,
                            "highScore": highScore
                        })
                    else:
                        regular.append({
                            "node": nodeName,
                            "highScore": highScore
                        })

        self._attr_extra_state_attributes = {
            "steel_path": steel_path,
            "regular": regular,
            "total_missions": total_missions
            }
        self._attr_native_value = total_completed_missions / total_missions
        self.async_write_ha_state()

# class ProfileMostUsedSensor(CoordinatorEntity, SensorEntity):
#     def __init__(self, coordinator, username, type):
#         super().__init__(coordinator)

#         self.username = username
#         self.type = type
#         self._name = username + " Most Used " + type.capitalize()
#         self._state = 0
#         self.attrs = {}
#         self._available = True
#         self.entity_id = f"sensor.warframe_{username}_most_used_{type}"

#         self._icon = "mdi:map-marker-path"

#     @property
#     def device_info(self) -> DeviceInfo:
#         """Return the device info."""
#         return DeviceInfo(
#             identifiers={(*profile_device_base_identifiers, self.username)},
#             name=profile_device_base_name + self.username
#         )

#     @property
#     def icon(self):
#         return self._icon

#     @property
#     def state_class(self) -> SensorStateClass:
#         """Handle string instances."""
#         return SensorStateClass.MEASUREMENT

#     @property
#     def name(self) -> str:
#         """Return the name of the entity."""
#         return self._name

#     @property
#     def state(self) -> int | None:
#         return self._state

#     @property
#     def extra_state_attributes(self) -> dict[str, Any]:
#         return self.attrs

#     @property
#     def native_value(self) -> int:
#         return self._state

#     @property
#     def unique_id(self):
#         """Return a unique ID."""
#         return f"sensor.warframe_{self.username}_most_used_{self.type}"

#     @callback
#     def _handle_coordinator_update(self):
#         weapons_data = (
#             self.coordinator.data.get(self.username, {}).get("weapons", [])
#         )
#         lookup = self.coordinator.data.get("lookup")

#         self.attrs.update()
#         self._state =
#         self.async_write_ha_state()


def _get_weapon_type(itemKey, lookup):
    print("get_weapon_type")

def _check_hard_mode(nodeKey):
    return True if nodeKey.endswith("_HM") else False

def _get_partial_lookup(to_lookup, lookup_table, default=None):
    to_lookup = to_lookup.lower()
    data = lookup_table.get(to_lookup)
    if data is not None:
        return data
    for lookup_key, data in lookup_table.items():
        ## if lookup key is substring
        if lookup_key.startswith(to_lookup) or to_lookup.startswith(lookup_key):
            return data
    for lookup_key, data in lookup_table.items():
        if lookup_key.startswith("/".join(to_lookup.split("/")[:-1])) or "/".join(to_lookup.split("/")[:-1]).startswith(lookup_key):
            return data
    return default
