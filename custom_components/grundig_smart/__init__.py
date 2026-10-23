"""The Grundig Smart TV integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GrundigApi
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
)
from .coordinator import GrundigCoordinator

PLATFORMS = [Platform.MEDIA_PLAYER, Platform.REMOTE, Platform.SELECT]


@dataclass
class GrundigRuntimeData:
    """Runtime data stored on the config entry."""

    api: GrundigApi
    coordinator: GrundigCoordinator


GrundigConfigEntry = ConfigEntry[GrundigRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: GrundigConfigEntry) -> bool:
    """Set up a Grundig TV from a config entry."""
    session = async_get_clientsession(hass)
    api = GrundigApi(
        session,
        entry.data[CONF_HOST],
        entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    coordinator = GrundigCoordinator(
        hass,
        api,
        entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    # Do not fail setup when the TV is in standby; the entities then simply
    # start as off and recover on the next successful poll.
    await coordinator.async_refresh()

    entry.runtime_data = GrundigRuntimeData(api=api, coordinator=coordinator)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: GrundigConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant,
    entry: GrundigConfigEntry,
) -> None:
    """Reload the entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
