from datetime import timedelta
import aiohttp
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)

from .const import (
    URL_BASE,
    URL_TRANSLATION_FACTIONS_ENDPOINT,
    URL_TRANSLATION_FISSURE_MODIFERS_ENDPOINT,
    URL_TRANSLATION_MISSION_TYPES_ENDPOINT,
    URL_TRANSLATION_OTHER_ENDPOINT,
    URL_TRANSLATION_SOL_NODES_ENDPOINT,
    URL_TRANSLATION_SORTIES_ENDPOINT,
    URL_TRANSLATION_SYNDICATES_ENDPOINT,
    URL_WORLD_STATE_ENDPOINT,
    URL_PRE_PROFILE_ENDPOINT,
    URL_STATS_ENDPOINT,
    URL_STATIC_ITEM_ENDPOINT
)


class WarframeStatsDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry):
        """Initialize the coordinator."""
        self._str_lookup = {}
        self.config = entry.data

        self.gottenInitData = False

        update_interval = timedelta(seconds=166666)
        super().__init__(
            hass,
            _LOGGER,
            name="Warframe Stats",
            update_interval=update_interval,
        )

    async def async_remove_entry(self, hass, entry) -> None:
        """Handle removal of an entry."""
        print("Closing")

    async def _async_update_data(self):
        toReturn = {}
        try:
            session = aiohttp.ClientSession()
            if not self.gottenInitData:
                # Get the static files
                # Build name lookup dictioary from multiple endpoints
                await self._get_init_data(session)
                await self._standardise_lookup()
                # Create custom lookup method for partial matches with starting with
                self.gottenInitData = True
            # normal update pos
            # If subscribed to worldstate then call api
            data = {}
            if self.config.get("worldstates"):
                data.update({"worldstates": await self._makeRequest(f'{URL_BASE}{URL_WORLD_STATE_ENDPOINT}', session)})
            if self.config.get("profiles"):
                user_data = {}
                for user in self.config.get("usernames"):
                    user_data.update({user: await self._makeRequest(f'{URL_BASE}{URL_PRE_PROFILE_ENDPOINT}{user}{URL_STATS_ENDPOINT}', session)})
                data.update({"profiles": user_data})
            if self.config.get("static_items"):
                data.update({"static_items": await self._makeRequest(f'{URL_BASE}{URL_STATIC_ITEM_ENDPOINT}', session)})
        finally:
            await session.close()

            toReturn.update({
                "lookup": self._str_lookup,
                "data": data
            })
            return toReturn



    async def _standardise_lookup(self):
        self._str_lookup = {k.lower(): v for k, v in self._str_lookup.items()}

    async def _get_init_data(self, session):
        # Sorties Modifiers
        await self._update_lookup_if_valid(
            await self._orginize_sorties_lookup(
                await self._makeRequest(f"{URL_BASE}{URL_TRANSLATION_SORTIES_ENDPOINT}", session)
            )
        )
        # Faction Names
        await self._update_lookup_if_valid(
            await self._makeRequest(f"{URL_BASE}{URL_TRANSLATION_FACTIONS_ENDPOINT}", session)
        )
        # Node Names
        await self._update_lookup_if_valid(
            await self._makeRequest(f"{URL_BASE}{URL_TRANSLATION_SOL_NODES_ENDPOINT}", session)
        )
        # Fissures
        await self._update_lookup_if_valid(
            await self._makeRequest(
                f"{URL_BASE}{URL_TRANSLATION_FISSURE_MODIFERS_ENDPOINT}", session
            )
        )
        # Syndicates (All including things like Ostrons and such)
        await self._update_lookup_if_valid(
            await self._makeRequest(f"{URL_BASE}{URL_TRANSLATION_SYNDICATES_ENDPOINT}", session)
        )
        # Mission Types
        await self._update_lookup_if_valid(
            await self._makeRequest(
                f"{URL_BASE}{URL_TRANSLATION_MISSION_TYPES_ENDPOINT}", session
            )
        )
        # Everything else
        await self._update_lookup_if_valid(
            await self._makeRequest(f"{URL_BASE}{URL_TRANSLATION_OTHER_ENDPOINT}", session)
        )

    async def _update_lookup_if_valid(self, data):
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, dict):
                if value.get("value"):
                    self._str_lookup.update({key: value})

    async def _get_partial_lookup(self, lookup, default=None):
        lookup = lookup.lower()
        data = self._str_lookup.get(lookup)
        if data is not None:
            return data
        for lookup_key, data in self._str_lookup.items():
            if lookup_key.startswith(lookup) or lookup.startswith(lookup_key):
                return data
        return default

    async def _orginize_sorties_lookup(self, sorties_data):
        orginized_sorties_data = {}
        for key, value in sorties_data.items():
            if isinstance(key, str) and isinstance(value, dict):
                if key == "modifierTypes":
                    for modifier_key, modifier_value in value.items():
                        sortie_modifier = orginized_sorties_data.get(modifier_key, {})
                        sortie_modifier.update({"value": modifier_value})
                        # This might be unessesary (idk how object ref work in python)
                        orginized_sorties_data.update({modifier_key:sortie_modifier})
                elif key == "modifierDescriptions":
                    for modifier_key, modifier_description in value.items():
                        sortie_modifier = orginized_sorties_data.get(modifier_key, {})
                        sortie_modifier.update({"description": modifier_description})
                        # This might be unessesary (idk how object ref work in python)
                        orginized_sorties_data.update({modifier_key:sortie_modifier})
                elif key == "bosses":
                    for boss_key, boss_value in value.items():
                        orginized_sorties_data.update({boss_key:{"value": boss_value}})
        return orginized_sorties_data

    async def _makeRequest(self, url, session):
        getHeaders = {}
        toReturn = {}

        try:
            async with session.get(
                url, headers=getHeaders, timeout=6
            ) as getResponse:
                if getResponse.status == 200:
                    return dict(await getResponse.json())
                return toReturn
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")
