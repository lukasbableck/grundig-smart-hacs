"""Shared entity base class for the Grundig Smart TV integration."""

from __future__ import annotations

import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import GrundigError
from .const import DOMAIN, MANUFACTURER, resolve_key
from .coordinator import GrundigCoordinator

POWER_OVERRIDE_SECONDS = 20


class GrundigEntity(CoordinatorEntity[GrundigCoordinator]):
    """Base class for Grundig entities."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: GrundigCoordinator,
        entry: ConfigEntry,
        tv_info: dict[str, Any],
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._tv_info = tv_info
        self._power_override: bool | None = None
        self._power_override_until = 0.0

        unique_id = entry.unique_id or entry.entry_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, unique_id)},
            manufacturer=MANUFACTURER,
            model=tv_info.get("name") or "SMART inter@ctive",
            name=entry.title,
            sw_version=tv_info.get("version"),
            configuration_url=f"http://{coordinator.api.host}:{coordinator.api.port}/",
        )

    @property
    def available(self) -> bool:
        """Keep entities available so the TV can be shown as off."""
        return True

    @property
    def is_on(self) -> bool:
        """Return the last known power state."""
        if (
            self._power_override is not None
            and time.monotonic() < self._power_override_until
        ):
            return self._power_override
        self._power_override = None
        return bool((self.coordinator.data or {}).get("reachable"))

    def _set_power_override(self, state: bool) -> None:
        self._power_override = state
        self._power_override_until = time.monotonic() + POWER_OVERRIDE_SECONDS

    async def async_send_key(self, key: str) -> None:
        """Send a named key or a raw keyid:keysymbol pair."""
        keyid, keysymbol = resolve_key(key)
        await self.coordinator.api.async_send_key(keyid, keysymbol)

    async def async_power(self, turn_on: bool) -> None:
        """Send the power key unless the TV is already in the wanted state."""
        if self.is_on == turn_on:
            return

        try:
            await self.async_send_key("POWER")
        except GrundigError as err:
            if turn_on:
                raise HomeAssistantError(
                    "The TV is not reachable over HTTP. Power-on only works if "
                    "the TV keeps port 8085 open in standby; otherwise use "
                    "Wake-on-LAN or an IR blaster."
                ) from err
            raise HomeAssistantError(
                "Could not send the power command to the TV."
            ) from err

        self._set_power_override(turn_on)
        self.async_write_ha_state()
