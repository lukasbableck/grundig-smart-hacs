"""Remote platform for the Grundig Smart TV integration."""

from __future__ import annotations

import asyncio
from typing import Any

from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import GrundigError
from .const import CONF_TV_INFO, resolve_key
from .coordinator import GrundigCoordinator
from .entity import GrundigEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Grundig remote."""
    runtime = entry.runtime_data
    async_add_entities(
        [
            GrundigRemote(
                runtime.coordinator,
                entry,
                entry.data.get(CONF_TV_INFO, {}),
            )
        ]
    )


class GrundigRemote(GrundigEntity, RemoteEntity):
    """Send arbitrary keys to the TV."""

    _attr_name = "Remote"

    def __init__(
        self,
        coordinator: GrundigCoordinator,
        entry: ConfigEntry,
        tv_info: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, entry, tv_info)
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_remote"

    async def async_turn_on(self) -> None:
        """Turn the TV on."""
        await self.async_power(True)

    async def async_turn_off(self) -> None:
        """Turn the TV off."""
        await self.async_power(False)

    async def async_send_command(self, command: str | list[str], **kwargs: Any) -> None:
        """Send one or more commands to the TV.

        Each command is either a key name such as ``UP`` or ``OK`` or a raw
        ``keyid:keysymbol`` pair such as ``-2475:-4020``.
        """
        commands = [command] if isinstance(command, str) else list(command)
        if not commands:
            return

        num_repeats = max(1, int(kwargs.get("num_repeats", 1)))
        delay_secs = min(5.0, max(0.0, float(kwargs.get("delay_secs", 0.4))))

        for command_index, raw_command in enumerate(commands):
            try:
                keyid, keysymbol = resolve_key(raw_command)
            except ValueError as err:
                raise HomeAssistantError(str(err)) from err

            for repeat in range(num_repeats):
                try:
                    await self.coordinator.api.async_send_key(keyid, keysymbol)
                except GrundigError as err:
                    raise HomeAssistantError(
                        f"Could not send {raw_command!r} to the TV."
                    ) from err
                if repeat < num_repeats - 1:
                    await asyncio.sleep(delay_secs)

            if command_index < len(commands) - 1:
                await asyncio.sleep(delay_secs)
