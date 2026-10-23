"""Media player platform for the Grundig Smart TV integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import GrundigError
from .const import CONF_TV_INFO
from .coordinator import GrundigCoordinator
from .entity import GrundigEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Grundig media player."""
    runtime = entry.runtime_data
    async_add_entities(
        [
            GrundigMediaPlayer(
                runtime.coordinator,
                entry,
                entry.data.get(CONF_TV_INFO, {}),
            )
        ]
    )


class GrundigMediaPlayer(GrundigEntity, MediaPlayerEntity):
    """Representation of a Grundig SMART inter@ctive TV."""

    _attr_name = None

    def __init__(
        self,
        coordinator: GrundigCoordinator,
        entry: ConfigEntry,
        tv_info: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, entry, tv_info)
        self._attr_is_volume_muted = False

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        """Return the features supported by this TV."""
        return (
            MediaPlayerEntityFeature.TURN_ON
            | MediaPlayerEntityFeature.TURN_OFF
            | MediaPlayerEntityFeature.VOLUME_UP
            | MediaPlayerEntityFeature.VOLUME_DOWN
            | MediaPlayerEntityFeature.VOLUME_MUTE
            | MediaPlayerEntityFeature.CHANNEL_UP
            | MediaPlayerEntityFeature.CHANNEL_DOWN
            | MediaPlayerEntityFeature.PLAY_MEDIA
        )

    @property
    def state(self) -> MediaPlayerState:
        """Return the power state derived from reachability."""
        return MediaPlayerState.ON if self.is_on else MediaPlayerState.OFF

    @property
    def media_title(self) -> str | None:
        """Return the current channel name."""
        channel = (self.coordinator.data or {}).get("channel") or {}
        return channel.get("name") or None

    @property
    def is_volume_muted(self) -> bool:
        """Return the optimistic mute state."""
        return self._attr_is_volume_muted

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the current channel details."""
        channel = (self.coordinator.data or {}).get("channel") or {}
        attributes: dict[str, Any] = {}
        if channel:
            attributes["channel_number"] = channel.get("channelNumber")
            attributes["service_type"] = channel.get("serviceType")
            attributes["channel_source"] = channel.get("source")
        attributes["tv_name"] = self._tv_info.get("name")
        attributes["firmware"] = self._tv_info.get("version")
        return attributes

    async def async_turn_on(self) -> None:
        """Turn the TV on."""
        await self.async_power(True)

    async def async_turn_off(self) -> None:
        """Turn the TV off."""
        await self.async_power(False)

    async def async_volume_up(self) -> None:
        """Increase the volume by one step."""
        await self._async_key("VOLUME_UP")

    async def async_volume_down(self) -> None:
        """Decrease the volume by one step."""
        await self._async_key("VOLUME_DOWN")

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute or unmute the TV (the API only offers a toggle)."""
        if mute == self._attr_is_volume_muted:
            return
        await self._async_key("MUTE")
        self._attr_is_volume_muted = mute
        self.async_write_ha_state()

    async def async_channel_up(self) -> None:
        """Switch to the next channel."""
        await self._async_key("CHPLUS")

    async def async_channel_down(self) -> None:
        """Switch to the previous channel."""
        await self._async_key("CHMINUS")

    async def async_play_media(
        self,
        media_type: str,
        media_id: str,
        **kwargs: Any,
    ) -> None:
        """Switch to a channel by number or name."""
        if media_type not in ("channel", "tv_channel"):
            raise HomeAssistantError(
                f"Unsupported media type {media_type!r}; use 'channel'."
            )

        requested = str(media_id).strip()
        try:
            channels = await self.coordinator.api.async_get_channel_list()
        except GrundigError:
            channels = []

        if requested.isdigit():
            number = int(requested)
            match = next(
                (
                    channel
                    for channel in channels
                    if channel.get("channelNumber") == number
                ),
                None,
            )
        else:
            match = next(
                (
                    channel
                    for channel in channels
                    if str(channel.get("name", "")).casefold()
                    == requested.casefold()
                ),
                None,
            )
            if match is None:
                raise HomeAssistantError(
                    f"Channel {requested!r} was not found on the TV."
                )
            channel_number = match.get("channelNumber")
            if channel_number is None:
                raise HomeAssistantError(
                    f"Channel {requested!r} has no number on the TV."
                )
            number = int(channel_number)

        service_type = (match or {}).get("serviceType") or "DTV"
        try:
            await self.coordinator.api.async_set_channel(number, service_type)
        except GrundigError as err:
            raise HomeAssistantError(
                f"Could not switch to channel {number}."
            ) from err

        await self.coordinator.async_request_refresh()

    async def _async_key(self, key: str) -> None:
        """Send a key and translate API errors for Home Assistant."""
        try:
            await self.async_send_key(key)
        except GrundigError as err:
            raise HomeAssistantError(
                f"Could not send {key!r} to the TV."
            ) from err
