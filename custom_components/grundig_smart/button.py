"""Button platform for the Grundig Smart TV integration."""

from __future__ import annotations

from typing import Any, Final

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import GrundigError
from .const import CONF_TV_INFO, KEY_MAP
from .coordinator import GrundigCoordinator
from .entity import GrundigEntity

KEY_NAMES: Final[dict[str, str]] = {
    "POWER": "Power",
    "VOLUME_UP": "Volume up",
    "VOLUME_DOWN": "Volume down",
    "MUTE": "Mute",
    "CHPLUS": "Channel up",
    "CHMINUS": "Channel down",
    "SELECT": "OK",
    "BACK": "Back",
    "EXIT": "Exit",
    "MENU": "Menu",
    "INFO": "Info",
    "TOOLS": "Tools",
    "EPG": "Guide",
    "INPUTSOURCE": "Source",
    "FAV": "Favorites",
    "TEXT": "Teletext",
    "SUBTITLE": "Subtitles",
    "AUDIO": "Audio",
    "RED": "Red",
    "GREEN": "Green",
    "YELLOW": "Yellow",
    "BLUE": "Blue",
    "UP": "Up",
    "DOWN": "Down",
    "LEFT": "Left",
    "RIGHT": "Right",
    "0": "0",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "PLAY": "Play",
    "PAUSE": "Pause",
    "STOP": "Stop",
    "RECORD": "Record",
    "FASTREWIND": "Rewind",
    "FASTFORWARD": "Fast forward",
    "PREVIOUS": "Previous",
    "NEXT": "Next",
    "RECORDLIST": "Record list",
    "NETFLIX": "Netflix",
    "INTERNET": "Internet (alternate)",
    "INTERNET_KY": "Internet",
    "3D": "3D",
}

KEY_ICONS: Final[dict[str, str]] = {
    "POWER": "mdi:power",
    "VOLUME_UP": "mdi:volume-plus",
    "VOLUME_DOWN": "mdi:volume-minus",
    "MUTE": "mdi:volume-mute",
    "CHPLUS": "mdi:chevron-up",
    "CHMINUS": "mdi:chevron-down",
    "SELECT": "mdi:check-circle-outline",
    "BACK": "mdi:arrow-left",
    "EXIT": "mdi:exit-to-app",
    "MENU": "mdi:menu",
    "INFO": "mdi:information-outline",
    "TOOLS": "mdi:wrench",
    "EPG": "mdi:television-guide",
    "INPUTSOURCE": "mdi:video-input-hdmi",
    "FAV": "mdi:star-outline",
    "TEXT": "mdi:text-box-outline",
    "SUBTITLE": "mdi:subtitles-outline",
    "AUDIO": "mdi:volume-high",
    "RED": "mdi:circle",
    "GREEN": "mdi:circle",
    "YELLOW": "mdi:circle",
    "BLUE": "mdi:circle",
    "UP": "mdi:arrow-up",
    "DOWN": "mdi:arrow-down",
    "LEFT": "mdi:arrow-left",
    "RIGHT": "mdi:arrow-right",
    "0": "mdi:numeric-0",
    "1": "mdi:numeric-1",
    "2": "mdi:numeric-2",
    "3": "mdi:numeric-3",
    "4": "mdi:numeric-4",
    "5": "mdi:numeric-5",
    "6": "mdi:numeric-6",
    "7": "mdi:numeric-7",
    "8": "mdi:numeric-8",
    "9": "mdi:numeric-9",
    "PLAY": "mdi:play",
    "PAUSE": "mdi:pause",
    "STOP": "mdi:stop",
    "RECORD": "mdi:record-circle",
    "FASTREWIND": "mdi:rewind",
    "FASTFORWARD": "mdi:fast-forward",
    "PREVIOUS": "mdi:skip-previous",
    "NEXT": "mdi:skip-next",
    "RECORDLIST": "mdi:format-list-bulleted",
    "NETFLIX": "mdi:netflix",
    "INTERNET": "mdi:web",
    "INTERNET_KY": "mdi:web",
    "3D": "mdi:video-3d",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one button per remote key."""
    runtime = entry.runtime_data
    tv_info = entry.data.get(CONF_TV_INFO, {})
    async_add_entities(
        [
            GrundigButton(runtime.coordinator, entry, tv_info, key)
            for key in KEY_MAP
        ]
    )


class GrundigButton(GrundigEntity, ButtonEntity):
    """A single key on the TV remote."""

    def __init__(
        self,
        coordinator: GrundigCoordinator,
        entry: ConfigEntry,
        tv_info: dict[str, Any],
        key: str,
    ) -> None:
        super().__init__(coordinator, entry, tv_info)
        self._key = key
        self._attr_name = KEY_NAMES.get(key, key.replace("_", " ").title())
        self._attr_unique_id = (
            f"{entry.unique_id or entry.entry_id}_{key.lower()}"
        )
        self._attr_icon = KEY_ICONS.get(key)

    async def async_press(self) -> None:
        """Press the key."""
        try:
            await self.async_send_key(self._key)
        except GrundigError as err:
            raise HomeAssistantError(
                f"Could not press {self._attr_name} on the TV."
            ) from err
