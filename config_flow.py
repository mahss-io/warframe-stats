"""Config flow for Warframe Stats integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    DOMAIN,
    CONF_WORLDSTATES,
    CONF_PROFILES,
    CONF_STATIC_ITEMS,
    CONF_ALERTS,
    CONF_ARCHON_HUNT,
    CONF_OPEN_WORLDS,
    CONF_RELAY_EVENTS,
    CONF_DEEP_ARCHIMEDEA,
    CONF_EARTH_TIME,
    CONF_EVENTS,
    CONF_FISSURES,
    CONF_INVASIONS,
    CONF_SORTIES,
    CONF_STEEL_PATH,
    CONF_VOID_TRADER,
    CONF_VARZIA,
    CONF_USERNAMES,
    CONF_TOTAL_ABILITIES_USED,
    CONF_TOTAL_ENEMIES_KILLED,
    CONF_MOST_SCANS,
    CONF_MOST_USED_WARFRAME,
    CONF_MOST_USED_PRIMARY,
    CONF_MOST_USED_SECONDARY,
    CONF_MOST_USED_MELEE,
    CONF_MOST_USED_COMPANION,
    CONF_CREDITS,
    CONF_RANK,
    CONF_DEATHS,
    CONF_TIME_PLAYED,
    CONF_STAR_CHART_COMPLETION,
    CONF_TOTAL_ITEMS,
    CONF_TOTAL_PRIME_ITEMS,
    CONF_NEWEST_WARFRAME
)
_LOGGER = logging.getLogger(__name__)

# TODO adjust the data schema to the data that you need
STEP_INIT_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_WORLDSTATES): bool,
        vol.Required(CONF_PROFILES): bool,
        vol.Required(CONF_STATIC_ITEMS): bool,
    }
)

STEP_WORLDSTATES_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ALERTS): bool,
        vol.Required(CONF_ARCHON_HUNT): bool,
        vol.Required(CONF_OPEN_WORLDS): bool,
        vol.Required(CONF_RELAY_EVENTS): bool,
        vol.Required(CONF_DEEP_ARCHIMEDEA): bool,
        vol.Required(CONF_EARTH_TIME): bool,
        vol.Required(CONF_EVENTS): bool,
        vol.Required(CONF_FISSURES): bool,
        vol.Required(CONF_INVASIONS): bool,
        vol.Required(CONF_SORTIES): bool,
        vol.Required(CONF_STEEL_PATH): bool,
        vol.Required(CONF_VOID_TRADER): bool,
        vol.Required(CONF_VARZIA): bool
    }
)

STEP_PROFILES_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAMES): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                multiple=True,
            ),
        ),
        vol.Required(CONF_TOTAL_ABILITIES_USED): bool,
        vol.Required(CONF_TOTAL_ENEMIES_KILLED): bool,
        vol.Required(CONF_MOST_SCANS): bool,
        vol.Required(CONF_MOST_USED_WARFRAME): bool,
        vol.Required(CONF_MOST_USED_PRIMARY): bool,
        vol.Required(CONF_MOST_USED_SECONDARY): bool,
        vol.Required(CONF_MOST_USED_MELEE): bool,
        vol.Required(CONF_MOST_USED_COMPANION): bool,
        vol.Required(CONF_CREDITS): bool,
        vol.Required(CONF_RANK): bool,
        vol.Required(CONF_DEATHS): bool,
        vol.Required(CONF_TIME_PLAYED): bool,
        vol.Required(CONF_STAR_CHART_COMPLETION): bool,
    }
)

STEP_STATIC_ITEMS_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_TOTAL_ITEMS): bool,
        vol.Required(CONF_TOTAL_PRIME_ITEMS): bool,
        vol.Required(CONF_NEWEST_WARFRAME): bool,
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass.

    TODO Remove this placeholder class and replace with things from your PyPI package.
    """

    def __init__(self, host: str) -> None:
        """Initialize."""
        self.host = host

    async def authenticate(self, username: str, password: str) -> bool:
        """Test if we can authenticate with the host."""
        return True


async def validate_init_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    if data.get('worldstates') == None:
        return False
    return True
async def validate_worldstates_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
        if data.get('alerts') == None:
            return False
        return True
async def validate_profiles_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
        if data.get('usernames') == None:
            return False
        return True
async def validate_static_items_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
        if data.get('total_items') == None:
            return False
        return True

class ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Warframe Stats."""

    VERSION = 1

    def __init__(self) -> None:
        """Create the config flow for a new integration."""
        self._worldstates: bool = False
        self._profiles: bool = False
        self._static_items: bool = False
        self._options: dict[str, Any] = {}

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        return await self.async_step_user(user_input)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                valid = await validate_init_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self._options.update(user_input)
                self._worldstates = user_input.get("worldstates")
                self._profiles = user_input.get("profiles")
                self._static_items = user_input.get("static_items")
                return await self.async_step_worldstates()

        return self.async_show_form(
            step_id="user", data_schema=STEP_INIT_DATA_SCHEMA, errors=errors
        )

    async def async_step_worldstates(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if self._worldstates:
            if user_input is not None:
                try:
                    valid = await validate_worldstates_input(self.hass, user_input)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except InvalidAuth:
                    errors["base"] = "invalid_auth"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    self._options.update(user_input)
                    return await self.async_step_profiles()

            return self.async_show_form(
                step_id="worldstates", data_schema=STEP_WORLDSTATES_DATA_SCHEMA, errors=errors
            )

        return await self.async_step_profiles()

    async def async_step_profiles(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if self._profiles:
            if user_input is not None:
                try:
                    valid = await validate_profiles_input(self.hass, user_input)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except InvalidAuth:
                    errors["base"] = "invalid_auth"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    self._options.update(user_input)
                    return await self.async_step_static_items()

            return self.async_show_form(
                step_id="profiles", data_schema=STEP_PROFILES_DATA_SCHEMA, errors=errors
            )

        return await self.async_step_static_items()

    async def async_step_static_items(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if self._static_items:
            if user_input is not None:
                try:
                    valid = await validate_static_items_input(self.hass, user_input)
                except CannotConnect:
                    errors["base"] = "cannot_connect"
                except InvalidAuth:
                    errors["base"] = "invalid_auth"
                except Exception:
                    _LOGGER.exception("Unexpected exception")
                    errors["base"] = "unknown"
                else:
                    self._options.update(user_input)
                    return self.async_create_entry(title="Warframe Stats", data=self._options)

            return self.async_show_form(
                step_id="static_items", data_schema=STEP_STATIC_ITEMS_DATA_SCHEMA, errors=errors
            )

        return self.async_create_entry(title="Warframe Stats", data=self._options)

class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
