"""The Warframe Stats integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import (
    WarframeProfileDataUpdateCoordinator,
    WarframeStaticDataUpdateCoordinator,
    WarframeWorldstateDataUpdateCoordinator,
)

# TODO List the platforms that you want to support.
# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]

from .const import DOMAIN

# TODO Create ConfigEntry type alias with API object
# TODO Rename type alias and update all entry annotations
type WarframeStatsConfigEntry = ConfigEntry[MyApi]  # noqa: F821


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: WarframeStatsConfigEntry) -> bool:
    """Set up Warframe Stats from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)
    staticDataCoordinator = WarframeStaticDataUpdateCoordinator(hass, entry)
    await staticDataCoordinator.async_config_entry_first_refresh()
    worldstateCoordinator = WarframeWorldstateDataUpdateCoordinator(hass, entry)
    await worldstateCoordinator.async_config_entry_first_refresh()
    # profileCoordinator = WarframeProfileDataUpdateCoordinator(hass, entry)
    # await profileCoordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    hass_data.update({'coordinator': [staticDataCoordinator, worldstateCoordinator]})
    hass.data[DOMAIN][entry.entry_id] = hass_data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: WarframeStatsConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
