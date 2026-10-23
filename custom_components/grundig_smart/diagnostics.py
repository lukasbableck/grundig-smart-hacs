"""Diagnostics support for the Grundig Smart TV integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_TV_INFO


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data = dict(entry.data)
    tv_info = dict(data.get(CONF_TV_INFO) or {})
    tv_info.pop("macaddress", None)
    data[CONF_TV_INFO] = tv_info

    return {
        "entry": {
            "data": data,
            "options": dict(entry.options),
        },
        "coordinator": entry.runtime_data.coordinator.data,
    }
