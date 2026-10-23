"""Shared entity base class for the Grundig Smart TV integration."""

from __future__ import annotations

import asyncio
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import GrundigError
from .const import (
    CONF_WOL_BROADCAST_ADDRESS,
    CONF_WOL_BROADCAST_PORT,
    CONF_WOL_ENABLED,
    CONF_WOL_SEND_POWER,
    CONF_WOL_TIMEOUT,
    DEFAULT_WOL_BROADCAST_ADDRESS,
    DEFAULT_WOL_BROADCAST_PORT,
    DEFAULT_WOL_ENABLED,
    DEFAULT_WOL_SEND_POWER,
    DEFAULT_WOL_TIMEOUT,
    DOMAIN,
    MANUFACTURER,
    resolve_key,
)
from .coordinator import GrundigCoordinator
from .wol import async_send_magic_packet

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

        self._mac = tv_info.get("macaddress")
        self._wol_enabled = bool(
            entry.options.get(CONF_WOL_ENABLED, DEFAULT_WOL_ENABLED)
        )
        self._wol_broadcast_address = entry.options.get(
            CONF_WOL_BROADCAST_ADDRESS,
            DEFAULT_WOL_BROADCAST_ADDRESS,
        )
        self._wol_broadcast_port = int(
            entry.options.get(
                CONF_WOL_BROADCAST_PORT,
                DEFAULT_WOL_BROADCAST_PORT,
            )
        )
        self._wol_timeout = int(
            entry.options.get(CONF_WOL_TIMEOUT, DEFAULT_WOL_TIMEOUT)
        )
        self._wol_send_power = bool(
            entry.options.get(CONF_WOL_SEND_POWER, DEFAULT_WOL_SEND_POWER)
        )

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
    def _tv_reachable(self) -> bool:
        """Return whether the last poll reached the TV."""
        return bool((self.coordinator.data or {}).get("reachable"))

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
        """Turn the TV on or off, using Wake-on-LAN when it is unreachable."""
        if self.is_on == turn_on:
            return

        if turn_on and not self._tv_reachable:
            await self._async_wake_on_lan()
            self._set_power_override(True)
            self.async_write_ha_state()
            return

        try:
            await self.async_send_key("POWER")
        except GrundigError as err:
            if turn_on:
                await self._async_wake_on_lan()
                self._set_power_override(True)
                self.async_write_ha_state()
                return
            raise HomeAssistantError(
                "Could not send the power command to the TV."
            ) from err

        self._set_power_override(turn_on)
        self.async_write_ha_state()

    async def _async_wake_on_lan(self) -> None:
        """Send a magic packet and wait for the TV's HTTP API to return."""
        if not self._wol_enabled:
            raise HomeAssistantError(
                "The TV is unreachable and Wake-on-LAN is disabled. Enable it "
                "in the integration options or use an IR blaster."
            )

        if not self._mac:
            raise HomeAssistantError(
                "The TV is unreachable and no MAC address is known, so "
                "Wake-on-LAN cannot be used."
            )

        try:
            await async_send_magic_packet(
                self.hass,
                self._mac,
                self._wol_broadcast_address,
                self._wol_broadcast_port,
            )
        except (OSError, ValueError) as err:
            raise HomeAssistantError(
                f"Could not send the Wake-on-LAN packet: {err}"
            ) from err

        deadline = time.monotonic() + self._wol_timeout

        # Phase 1: wait for the network stack. Some TVs wake only their NIC
        # and stay in standby, so /gettvinfo may answer before /getchannel.
        network_awake = False
        while time.monotonic() < deadline:
            await asyncio.sleep(1)
            try:
                async with asyncio.timeout(3):
                    await self.coordinator.api.async_get_tv_info()
            except (GrundigError, TimeoutError):
                continue
            network_awake = True
            break

        if not network_awake:
            raise HomeAssistantError(
                "The TV did not come online within "
                f"{self._wol_timeout} seconds after the Wake-on-LAN packet. "
                "Check that Wake-on-LAN is enabled on the TV, that the TV is "
                "connected by Ethernet, and that the broadcast address is correct."
            )

        if self._wol_send_power:
            # If /getchannel already answers, the TV is fully on and sending
            # POWER would turn it off again. Only send it if the TV is still
            # in its standby/network-only state.
            try:
                async with asyncio.timeout(5):
                    await self.coordinator.api.async_get_channel()
            except (GrundigError, TimeoutError):
                try:
                    await self.async_send_key("POWER")
                except GrundigError as err:
                    raise HomeAssistantError(
                        "The TV woke up, but the power key could not be sent."
                    ) from err
                await asyncio.sleep(1)

        # Phase 2: wait for the endpoint the coordinator uses, so the entity
        # really reports "on" rather than just "network reachable".
        while time.monotonic() < deadline:
            await asyncio.sleep(1)
            try:
                async with asyncio.timeout(3):
                    await self.coordinator.api.async_get_channel()
            except (GrundigError, TimeoutError):
                continue

            await self.coordinator.async_refresh()
            return

        raise HomeAssistantError(
            "The TV's network interface woke up, but its control API did not "
            f"respond within {self._wol_timeout} seconds. If the TV stays in "
            "standby, enable 'Send power key after Wake-on-LAN' in the "
            "integration options."
        )
