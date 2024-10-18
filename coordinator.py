from datetime import timedelta
import logging
import socket
import aiohttp

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.core import Event, callback, CALLBACK_TYPE
from homeassistant.const import CONF_HOST, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from yarl import URL

_LOGGER = logging.getLogger(__name__)

from .const import (
    URL_BASE,
    URL_TRANSLATION_FACTIONS_ENDPOINT,
    URL_TRANSLATION_FISSURE_MODIFERS_ENDPOINT,
    URL_TRANSLATION_MISSION_TYPES_ENDPOINT,
    URL_TRANSLATION_OTHER_ENDPOINT,
    URL_TRANSLATION_WARFRAME_ENDPOINT,
    URL_TRANSLATION_SOL_NODES_ENDPOINT,
    URL_TRANSLATION_SORTIES_ENDPOINT,
    URL_TRANSLATION_SYNDICATES_ENDPOINT,
    URL_WORLD_STATE_ENDPOINT,
    URL_PRE_PROFILE_ENDPOINT,
    URL_STATS_ENDPOINT,
    URL_STATIC_ITEM_ENDPOINT,
    URL_STATIC_DATA_LOOKUP,
    URL_STATIC_DATA_LOOKUP_QUERY_PARAMS,
    ITEM_SETS_TO_INCLUDE
)


class WarframeStaticDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        """Initialize the coordinator."""
        self.session = async_get_clientsession(hass)
        self.config = entry.data
        self.name_lookup = {}

        update_interval = timedelta(seconds=(3600 * 24))
        super().__init__(
            hass,
            _LOGGER,
            name="Warframe Static Data Updater",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        try:
            # await self._get_init_data(self.session)
            await self._get_item_data(self.session)
            await self._standardise_lookup()
        except Exception as err:
            print(err)

    async def _standardise_lookup(self):
        self.name_lookup = {k.lower(): v for k, v in self.name_lookup.items()}

    async def _get_item_data(self, session):
        static_data = await _makeRequest(f"{URL_BASE}{URL_STATIC_DATA_LOOKUP}{",".join(ITEM_SETS_TO_INCLUDE)}{URL_STATIC_DATA_LOOKUP_QUERY_PARAMS}", session)
        for item in static_data:
            match item.get("category"):
                case "Warframe":
                    # warframe
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                    # abilities
                    for ability in item.get("abilities", []):
                        self.name_lookup.update({
                        ability.get("uniqueName"): {
                            "value": ability.get("name"),
                            "description": ability.get("description")
                            }
                        })
                case "Archwing":
                    # archwing
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                    # abilities
                    for ability in item.get("abilities", []):
                        self.name_lookup.update({
                        ability.get("uniqueName"): {
                            "value": ability.get("name"),
                            "description": ability.get("description")
                            }
                        })
                case "Sentinels":
                    # sentinel
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                case "Pets":
                    # pet
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                case "Primary":
                    # primary
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                case "Secondary":
                    # secondary
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                case "Melee":
                    # melee
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                case "Arch-Gun":
                    # arch-gun
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                case "Arch-Melee":
                    # arch-melee
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                case "Enemy":
                    # enemy
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "description": item.get("description")
                        }
                    })
                case "Node":
                    # node
                    self.name_lookup.update({
                        item.get("uniqueName"): {
                            "value": item.get("name"),
                            "systemName": item.get("systemName")
                        }
                    })

    async def _get_init_data(self, session):
        # Sorties Modifiers
        await self._update_lookup_if_valid(
            await self._orginize_sorties_lookup(
                await _makeRequest(
                    f"{URL_BASE}{URL_TRANSLATION_SORTIES_ENDPOINT}", session
                )
            )
        )
        # Warframe Abilities
        await self._update_lookup_if_valid(
            await self._orginize_warframe_abilitiy_lookup(
                await _makeRequest(
                    f"{URL_BASE}{URL_TRANSLATION_WARFRAME_ENDPOINT}", session
                )
            )
        )
        # Faction Names
        await self._update_lookup_if_valid(
            await _makeRequest(
                f"{URL_BASE}{URL_TRANSLATION_FACTIONS_ENDPOINT}", session
            )
        )
        # Node Names
        await self._update_lookup_if_valid(
            await _makeRequest(
                f"{URL_BASE}{URL_TRANSLATION_SOL_NODES_ENDPOINT}", session
            )
        )
        # Fissures
        await self._update_lookup_if_valid(
            await _makeRequest(
                f"{URL_BASE}{URL_TRANSLATION_FISSURE_MODIFERS_ENDPOINT}", session
            )
        )
        # Syndicates (All including things like Ostrons and such)
        await self._update_lookup_if_valid(
            await _makeRequest(
                f"{URL_BASE}{URL_TRANSLATION_SYNDICATES_ENDPOINT}", session
            )
        )
        # Mission Types
        await self._update_lookup_if_valid(
            await _makeRequest(
                f"{URL_BASE}{URL_TRANSLATION_MISSION_TYPES_ENDPOINT}", session
            )
        )
        # Everything else
        await self._update_lookup_if_valid(
            await _makeRequest(f"{URL_BASE}{URL_TRANSLATION_OTHER_ENDPOINT}", session)
        )

    async def _update_lookup_if_valid(self, data):
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, dict):
                if value.get("value"):
                    self.name_lookup.update({key: value})

    async def _orginize_sorties_lookup(self, sorties_data):
        orginized_sorties_data = {}
        for key, value in sorties_data.items():
            if isinstance(key, str) and isinstance(value, dict):
                if key == "modifierTypes":
                    for modifier_key, modifier_value in value.items():
                        sortie_modifier = orginized_sorties_data.get(modifier_key, {})
                        sortie_modifier.update({"value": modifier_value})
                        # This might be unessesary (idk how object ref work in python)
                        orginized_sorties_data.update({modifier_key: sortie_modifier})
                elif key == "modifierDescriptions":
                    for modifier_key, modifier_description in value.items():
                        sortie_modifier = orginized_sorties_data.get(modifier_key, {})
                        sortie_modifier.update({"description": modifier_description})
                        # This might be unessesary (idk how object ref work in python)
                        orginized_sorties_data.update({modifier_key: sortie_modifier})
                elif key == "bosses":
                    for boss_key, boss_value in value.items():
                        orginized_sorties_data.update({boss_key: {"value": boss_value}})
        return orginized_sorties_data

    async def _orginize_warframe_abilitiy_lookup(self, warframe_data):
        orginized_warframe_ability_data = {}
        for warframe_entity in warframe_data:
            if isinstance(warframe_entity, dict):
                abilities = warframe_entity.get("abilities")
                if abilities and isinstance(abilities, list):
                    for ability in abilities:
                        ability_data = {
                            "value": ability.get("name"),
                            "description": ability.get("description"),
                        }
                        orginized_warframe_ability_data.update(
                            {ability.get("uniqueName"): ability_data}
                        )
        return orginized_warframe_ability_data


class WarframeProfileDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        """Initialize the coordinator."""
        self.session = async_get_clientsession(hass)
        self.config = entry.data

        update_interval = timedelta(seconds=3600)
        super().__init__(
            hass,
            _LOGGER,
            name="Warframe Profile Updater",
            update_interval=update_interval,
        )

    async def _async_update_data(self):
        user_data = {}
        for user in self.config.get("usernames", []):
            user_data.update(
                {
                    user: await _makeRequest(
                        f"{URL_BASE}{URL_PRE_PROFILE_ENDPOINT}{user}{URL_STATS_ENDPOINT}",
                        self.session,
                    )
                }
            )
        return user_data


class WarframeWorldstateDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        """Initialize the coordinator."""
        self.session = async_get_clientsession(hass)
        self.config = entry.data
        self.world_state_data = None
        self._client: aiohttp.ClientWebSocketResponse | None = None
        self.unsub: CALLBACK_TYPE | None = None

        update_interval = timedelta(seconds=10)
        super().__init__(
            hass,
            _LOGGER,
            name="Warframe Stats",
            update_interval=update_interval,
        )

    async def _async_setup(self):
        self.world_state_data = await _makeRequest(
            f"{URL_BASE}{URL_WORLD_STATE_ENDPOINT}", self.session
        )

    @callback
    def _use_websocket(self) -> None:
        """Use WebSocket for updates, instead of polling."""

        async def listen() -> None:
            """Listen for state changes via WebSocket."""
            try:
                await self._connect()
            except Exception as err:
                self.logger.info(err)
                return

            try:
                await self._listen()
            except Exception as err:
                self.last_update_success = False
                self.async_update_listeners()
                self.logger.error(err)

            # Ensure we are disconnected
            await self._disconnect()
            if self.unsub:
                self.unsub()
                self.unsub = None

        async def close_websocket(_: Event) -> None:
            """Close WebSocket connection."""
            self.unsub = None
            await self._disconnect()

        # Clean disconnect WebSocket on Home Assistant shutdown
        self.unsub = self.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, close_websocket
        )

        # Start listening
        self.config_entry.async_create_background_task(
            self.hass, listen(), "warframe-ws-listen"
        )

    async def _connect(self):

        if self._client is not None and not self._client.closed:
            return

        url = URL.build(
            scheme="ws", host="api.warframestat.us", port=80, path="/socket"
        )

        try:
            self._client = await self.session.ws_connect(
                url=url, heartbeat=30
            )
        except (
            aiohttp.WSServerHandshakeError,
            aiohttp.ClientConnectionError,
            socket.gaierror,
        ):
            msg = (
                "Error occurred while communicating with Warframe API"
                " on WebSocket at api.warframestat.us"
            )
            self.logger.error(msg)

    async def _listen(self):
        self.logger.info("_listen")
        if not self._client or not (self._client is not None and not self._client.closed):
            msg = "Not connected to a Warframe WebSocket"
            self.logger.info(msg)

        while not self._client.closed:
            message = await self._client.receive()

            if message.type == aiohttp.WSMsgType.ERROR:
                self.logger.error(self._client.exception())

            if message.type == aiohttp.WSMsgType.TEXT:
                message_data = message.json()
                if message_data.get("event") == "ws:update":
                    if message_data.get("packet").get("language") == "en":
                        self.world_state_data = message_data.get("packet").get("data")

            if message.type in (
                aiohttp.WSMsgType.CLOSE,
                aiohttp.WSMsgType.CLOSED,
                aiohttp.WSMsgType.CLOSING,
            ):
                msg = "Connection to the Warframe WebSocket on api.warframestat.us has been closed"
                self.logger.error(self._client.exception())
                self.logger.error(msg)

    async def _disconnect(self):
        self.logger.info("_disconnect")
        await self._client.close()

    async def _async_update_data(self):
        if (not (self._client is not None and not self._client.closed)
            and not self.unsub
        ):
            self._use_websocket()

        return self.world_state_data


async def _makeRequest(url, session):
    getHeaders = {}
    toReturn = {}

    try:
        async with session.get(url, headers=getHeaders, timeout=20) as getResponse:
            if getResponse.status == 200:
                return await getResponse.json()
    except Exception as err:
        raise UpdateFailed(f"Error fetching data: {err}")
    return toReturn
