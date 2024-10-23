"""Platform for sensor integration."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import MATCH_ALL, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .coordinator import (
    WarframeStaticDataUpdateCoordinator,
    WarframeWorldstateDataUpdateCoordinator,
)

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1

IGNORED_STATES = {STATE_UNAVAILABLE, STATE_UNKNOWN}

location_to_people_map = {
    "cetus": "ostrons",
    "cambion": "entrati",
    "zariman": "the holdfasts",
    "vallis": "solaris united"
}

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
    "companion",
    "companion-weapon",
    "archwing",
    "arch-melee",
    "arch-gun"
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
        sensors.append(LastUpdateSensor(worldstateCoordinator, staticDataCoordinator))
        sensors.append(AlertSensor(worldstateCoordinator))
        sensors.append(ArchonHuntSensor(worldstateCoordinator))
        cycle_keys = []
        for key in worldstateCoordinator.data.keys():
            if key.endswith("Cycle"):
                cycle_keys.append(key)
        for world_key in cycle_keys:
            sensors.append(WorldSensor(worldstateCoordinator, world_key))
        sensors.append(RelayEventSensor(worldstateCoordinator))
        sensors.append(EventSensor(worldstateCoordinator))
        sensors.append(FissureSensor(worldstateCoordinator, "regular"))
        sensors.append(FissureSensor(worldstateCoordinator, "steel_path"))
        sensors.append(FissureSensor(worldstateCoordinator, "void_storm"))
        sensors.append(InvasionSensor(worldstateCoordinator))
        sensors.append(SortieSensor(worldstateCoordinator))
        sensors.append(SteelPathSensor(worldstateCoordinator))
        sensors.append(VoidTraderSensor(worldstateCoordinator))
        sensors.append(VarziaSensor(worldstateCoordinator))
    if config.get("profiles"):
        for username in config.get("profiles"):
            sensors.append(AbilitiesSensor(profileCoordinator, username, staticDataCoordinator))
            sensors.append(EnemiesSensor(profileCoordinator, username, staticDataCoordinator))
            sensors.append(ScansSensor(profileCoordinator, username, staticDataCoordinator))
            sensors.append(CreditSensor(profileCoordinator, username))
            sensors.append(RankSensor(profileCoordinator, username))
            sensors.append(DeathSensor(profileCoordinator, username, staticDataCoordinator))
            sensors.append(TimePlayedSensor(profileCoordinator, username))
            sensors.append(StarChartSensor(profileCoordinator, username, staticDataCoordinator))
            for type in most_used_types:
                sensors.append(MostUsedSensor(profileCoordinator, username, staticDataCoordinator, type))

    async_add_entities(sensors, True)

class BaseWarframeSensor(CoordinatorEntity, RestoreSensor, SensorEntity):
    _attr_icon = "mdi:controller"
    _attr_native_value: float | None = None
    _attr_extra_state_attributes: dict | None = {}
    _unrecorded_attributes = frozenset({MATCH_ALL})

    _base_id = "sensor.warframe_"

    def __init__(self, coordinator):
        super().__init__(coordinator)

    async def async_added_to_hass(self) -> None:
        """Restore state on startup."""
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        last_sensor_data = await self.async_get_last_sensor_data()

        if not last_state or not last_sensor_data or last_state.state in IGNORED_STATES:
            return

        self._attr_native_value = last_sensor_data.native_value

class WorldStateSesnor(BaseWarframeSensor):
    _attr_icon = "mdi:earth"
    _worldstate_name = "worldstate_"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_device_info = worldstate_device

class ProfileSensor(BaseWarframeSensor):
    _attr_icon = "mdi:earth"

    def __init__(self, coordinator, username):
        super().__init__(coordinator)

        self.username = username

        self._attr_device_info = DeviceInfo(
            identifiers={(*profile_device_base_identifiers, username)},
            name=profile_device_base_name + username
        )

    async def async_added_to_hass(self) -> None:
        """Restore state on startup."""
        await super().async_added_to_hass()


class AlertSensor(WorldStateSesnor):
    _attr_icon = "mdi:alert"
    _attr_native_value: int | None = 0
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Alert"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}alerts"
        self.entity_id = self._attr_unique_id

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
        self._attr_extra_state_attributes = {"missions": missions}
        self._attr_native_value = alert_count
        self.async_write_ha_state()

class ArchonHuntSensor(WorldStateSesnor):
    _attr_icon = "mdi:calendar-week"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Archon Hunt"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}archon_hunt"
        self.entity_id = self._attr_unique_id

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
        self._attr_extra_state_attributes = {"missions": missions}
        self._attr_native_value = state
        self.async_write_ha_state()

class WorldSensor(WorldStateSesnor):
    _attr_icon = "mdi:earth"

    def __init__(self, coordinator, world_key):
        super().__init__(coordinator)

        self.world_name = world_key.replace("Cycle", "")
        self.world_key = world_key
        self.syndicate = location_to_people_map.get(self.world_name.lower())
        self._attr_name = self.world_name.capitalize() + " Cycle"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}{self.world_name}_cycle"
        self.entity_id = self._attr_unique_id

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
        syndicate_mission_data = (
            self.coordinator.data.get("syndicateMissions", [])
        )

        bounty_list = []

        for syndicate in syndicate_mission_data:
            if self.syndicate == syndicate.get("syndicate").lower():
                for job in syndicate.get("jobs", []):
                    bounty_list.append({
                        "name": job.get("type"),
                        "level_range": " - ".join(map(str, job.get("enemyLevels", []))),
                        "stages": len(job.get("standingStages")),
                        "rewards": job.get("rewardPool",[])
                    })
        self._attr_extra_state_attributes = {"bounties": bounty_list} if len(bounty_list) != 0 else {}
        self._attr_native_value = world_state_data.get("state")
        self.async_write_ha_state()

class RelayEventSensor(WorldStateSesnor):
    _attr_icon = "mdi:calendar-alert"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Relay Events"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}relay_events"
        self.entity_id = self._attr_unique_id

    @callback
    def _handle_coordinator_update(self):
        relay_event_data = (
            self.coordinator.data.get("constructionProgress", {})
        )

        fomorian = float(relay_event_data.get("fomorianProgress", "0"))
        razorback = float(relay_event_data.get("razorbackProgress", "0"))

        self._attr_extra_state_attributes = {"fomorian": fomorian,"razorback": razorback}
        self._attr_native_value = "Ongoing" if fomorian >= 100 or razorback >= 100 else "None"
        self.async_write_ha_state()

class EventSensor(WorldStateSesnor):
    _attr_icon = "mdi:calendar-star"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Events"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}events"
        self.entity_id = self._attr_unique_id

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("events", {})
        )

        event_count = 0
        event_data = []
        for event in _data:
            event_count += 1
            event_data.append({
                "name": event.get("description"),
                "ends": event.get("expiry")
                })


        self._attr_extra_state_attributes = {"events": event_data}
        self._attr_native_value = event_count
        self.async_write_ha_state()

class FissureSensor(WorldStateSesnor):
    _attr_icon = "mdi:ballot-outline"
    _attr_native_value: int | None = 0
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, fissure_type):
        super().__init__(coordinator)

        self.fissure_type = fissure_type
        self._attr_name = fissure_type.capitalize().replace("_", " ") + " Fissures"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}{fissure_type}_fissures"
        self.entity_id = self._attr_unique_id

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
                elif (fissure.get("isHard") == False and fissure.get("isStorm") == False) and self.fissure_type == "regular":
                    count += 1
                    data.append({
                        "node": fissure.get("node"),
                        "missionType": fissure.get("missionType"),
                        "enemy": fissure.get("enemy"),
                        "tier": fissure.get("tier")
                    })
        self._attr_extra_state_attributes = {"fissures":data}
        self._attr_native_value = count
        self.async_write_ha_state()

class InvasionSensor(WorldStateSesnor):
    _attr_icon = "mdi:ammunition"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Invasions"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}invasions"
        self.entity_id = self._attr_unique_id

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("invasions", {})
        )

        count = 0
        data = []
        for invasion in _data:
            if not invasion.get("completed"):
                count += 1
                data.append({
                    "node": invasion.get("node"),
                    "rewardTypes": invasion.get("rewardTypes"),
                    "enemy": invasion.get("defender").get("faction")
                })
        self._attr_extra_state_attributes = {"invasions":data}
        self._attr_native_value = count
        self.async_write_ha_state()

class SortieSensor(WorldStateSesnor):
    _attr_icon = "mdi:calendar-today"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Sorties"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}sorties"
        self.entity_id = self._attr_unique_id

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

        self._attr_extra_state_attributes = {"missions": missions_data}
        self._attr_native_value = state
        self.async_write_ha_state()

class SteelPathSensor(WorldStateSesnor):
    _attr_icon = "mdi:calendar-week"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Steel Path Honors"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}steel_path_teshin"
        self.entity_id = self._attr_unique_id

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("steelPath", {})
        )

        self._attr_native_value = _data.get("currentReward", {}).get("name")
        self.async_write_ha_state()

class VoidTraderSensor(WorldStateSesnor):
    _attr_icon = "mdi:storefront-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Void Trader"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}void_trader"
        self.entity_id = self._attr_unique_id

    @callback
    def _handle_coordinator_update(self):
        _data = (
            self.coordinator.data.get("voidTrader", {})
        )

        if _data.get("active"):
            self._attr_native_value = "Active"
            self._attr_extra_state_attributes = {"inventory": _data.get("inventory")}
        else:
            self._attr_native_value = "Inactive"
            self._attr_extra_state_attributes = {"inventory": []}
        self.async_write_ha_state()

class VarziaSensor(WorldStateSesnor):
    _attr_icon = "mdi:storefront-outline"

    def __init__(self, coordinator):
        super().__init__(coordinator)

        self._attr_name = "Primed Resurgence"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}prime_resurgence_rotation"
        self.entity_id = self._attr_unique_id

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

        self._attr_extra_state_attributes = {"items":data}
        self._attr_native_value = count
        self.async_write_ha_state()

class LastUpdateSensor(WorldStateSesnor):
    _attr_icon = "mdi:newspaper"

    def __init__(self, coordinator: WarframeWorldstateDataUpdateCoordinator, staticDataCoordinator: WarframeStaticDataUpdateCoordinator):
        super().__init__(coordinator)

        self.staticDataCoordinator = staticDataCoordinator
        self._attr_name = "Last Update"
        self._attr_unique_id = f"{self._base_id}{self._worldstate_name}last_update"
        self.entity_id = self._attr_unique_id

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

        if self._attr_native_value != newest_news:
            self.hass.async_create_task(self.staticDataCoordinator.async_refresh())

        self._attr_native_value = newest_news
        self.async_write_ha_state()


class AbilitiesSensor(ProfileSensor):
    _attr_icon = "mdi:exclamation-thick"

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator, username)

        self.static_data = staticDataCoordinator
        self._attr_name = self.username + " Abilities Used"
        self._attr_unique_id = f"sensor.warframe_{self.username}_abilities_used"
        self.entity_id = self._attr_unique_id

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
            ability_name = self.static_data.name_lookup.get(key.lower())
            ability_count += used
            abilities_used.append({
                "name": ability_name.get("value") if isinstance(ability_name, dict) else key,
                "used": used
            })

        self._attr_extra_state_attributes = {"abilities": abilities_used}
        self._attr_native_value = ability_count
        self.async_write_ha_state()

class EnemiesSensor(ProfileSensor):
    _attr_icon = "mdi:ammunition"

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator, username)

        self.static_data = staticDataCoordinator
        self._attr_name = username + " Enemies Killed"
        self._attr_unique_id = f"sensor.warframe_{username}_enemies_killed"
        self.entity_id = self._attr_unique_id

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
            enemy_name = self.static_data.name_lookup.get(key.lower())
            enemies_killed_count += killed
            enemies_killed.append({
                "name": enemy_name.get("value") if isinstance(enemy_name, dict) else key,
                "killed": killed
            })

        self._attr_extra_state_attributes = {"enemies_killed": enemies_killed}
        self._attr_native_value = enemies_killed_count
        self.async_write_ha_state()

class ScansSensor(ProfileSensor):
    _attr_icon = "mdi:skull-scan-outline"

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator, username)

        self.static_data = staticDataCoordinator
        self._attr_name = username + " Most Scans"
        self._attr_unique_id = f"sensor.warframe_{username}_most_scans"
        self.entity_id = self._attr_unique_id

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
            item_name = self.static_data.name_lookup.get(key.lower())
            if max_scan_amount < scans:
                max_scan_amount = scans
                max_scan_item = item_name.get("value") if isinstance(item_name, dict) else key

            items_scanned.append({
                "name": item_name.get("value") if isinstance(item_name, dict) else key,
                "scans": scans
            })

        self._attr_extra_state_attributes = {"max_scanned": {"name":max_scan_item, "scans": max_scan_amount}, "items_scanned": items_scanned}
        self._attr_native_value = max_scan_item
        self.async_write_ha_state()

class CreditSensor(ProfileSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:micro-sd"

    def __init__(self, coordinator, username):
        super().__init__(coordinator, username)

        self._attr_name = username + " Total Credits"
        self._attr_unique_id = f"sensor.warframe_{username}_total_credits"
        self.entity_id = self._attr_unique_id

    @callback
    def _handle_coordinator_update(self):
        credit_data = (
            self.coordinator.data.get(self.username, {}).get("income", 0)
        )
        time_played_seconds_data = (
            self.coordinator.data.get(self.username, {}).get("timePlayedSec", 0.0)
        )

        self._attr_extra_state_attributes = {"credits_per_hour": 0 if time_played_seconds_data == 0.0 else (credit_data/((time_played_seconds_data/60.0)/60.0))}
        self._attr_native_value = credit_data
        self.async_write_ha_state()

class RankSensor(ProfileSensor):
    _attr_icon = "mdi:chevron-triple-up"

    def __init__(self, coordinator, username):
        super().__init__(coordinator, username)

        self._attr_name = username + " Rank"
        self._attr_unique_id = f"sensor.warframe_{username}_rank"
        self.entity_id = self._attr_unique_id

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

        # self._attr_extra_state_attributes.update({"rank_per_day": rank_data/(((time_played_seconds_data/60)/60)/24)})
        self._attr_native_value = ("Legendary " if is_legendary else "") + str(rank)
        self.async_write_ha_state()

class DeathSensor(ProfileSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:robot-dead-outline"

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator, username)

        self.static_data = staticDataCoordinator
        self._attr_name = username + " Deaths"
        self._attr_unique_id = f"sensor.warframe_{username}_deaths"
        self.entity_id = self._attr_unique_id

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
                enemy_name = self.static_data.name_lookup.get(key.lower())
                enemies_that_killed_player.append({
                    "name": enemy_name.get("value") if isinstance(enemy_name, dict) else key,
                    "deaths": deaths
                })

        self._attr_extra_state_attributes = {"player_kills": enemies_that_killed_player}
        self._attr_native_value = death_data
        self.async_write_ha_state()

class TimePlayedSensor(ProfileSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-alert-outline"

    def __init__(self, coordinator, username):
        super().__init__(coordinator, username)

        self._attr_name = username + " Time Played"
        self._attr_unique_id = f"sensor.warframe_{username}_time_played"
        self.entity_id = self._attr_unique_id

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

        self._attr_extra_state_attributes = {
            "seconds_played": seconds_played,
            "minutes_played": minutes_played,
            "hours_played": hours_played,
            "days_played": days_played,
            "months_played": months_played,
            }
        self._attr_native_value = round(hours_played, 2)
        self.async_write_ha_state()

class StarChartSensor(ProfileSensor):
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:map-marker-path"

    def __init__(self, coordinator, username, staticDataCoordinator):
        super().__init__(coordinator, username)

        self.static_data = staticDataCoordinator
        self._attr_name = username + " Star Chart Completion"
        self._attr_unique_id = f"sensor.warframe_{username}_star_chart_completion"
        self.entity_id = self._attr_unique_id

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
            nodeName = self.static_data.name_lookup.get((nodeKey[:-3] if _check_hard_mode(nodeKey) else nodeKey).lower() )
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
        self._attr_native_value = total_completed_missions / total_missions if total_missions else 0
        self.async_write_ha_state()

class MostUsedSensor(ProfileSensor):
    _attr_icon = "mdi:chart-donut"

    def __init__(self, coordinator, username, staticDataCoordinator, type):
        super().__init__(coordinator, username)

        self.static_data = staticDataCoordinator
        self.type = type
        self._attr_name = username + " Most Used " + type.capitalize()
        self._attr_unique_id = f"sensor.warframe_{username}_most_used_{type}"
        self.entity_id = self._attr_unique_id

    @callback
    def _handle_coordinator_update(self):
        weapon_data = (
            self.coordinator.data.get(self.username, {}).get("weapons", [])
        )
        lookup = self.static_data.name_lookup

        most_used_key = ""
        most_equip_time = 0

        weapons = []

        for item in weapon_data:
            item_info = lookup.get(item.get("uniqueName").lower(), {})
            if (item_info.get("type") and item_info.get("type") == self.type):
                equip_time = item.get("equiptime", 0.0)
                weapons.append(item | {"name": item_info.get("value", item.get("uniqueName", "Unknown"))})
                if most_equip_time < equip_time:
                    most_equip_time = equip_time
                    most_used_key = item.get("uniqueName")

        self._attr_extra_state_attributes = {self.type: weapons}
        self._attr_native_value =_get_partial_lookup(most_used_key, lookup, {}).get("value")
        self.async_write_ha_state()

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
