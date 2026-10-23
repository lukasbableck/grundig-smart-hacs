"""Select platform for the Grundig Smart TV integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import GrundigError
from .const import CONF_TV_INFO, HDMI_INPUTS
from .coordinator import GrundigCoordinator
from .entity import GrundigEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Grundig selects."""
    runtime = entry.runtime_data
    tv_info = entry.data.get(CONF_TV_INFO, {})
    async_add_entities(
        [
            GrundigChannelSelect(runtime.coordinator, entry, tv_info),
            GrundigSourceSelect(runtime.coordinator, entry, tv_info),
        ]
    )


class GrundigSourceSelect(GrundigEntity, SelectEntity):
    """Switch the TV to one of its HDMI inputs."""

    _attr_name = "Source"
    _attr_icon = "mdi:video-input-hdmi"
    _attr_options = list(HDMI_INPUTS)
    _attr_current_option: str | None = None

    def __init__(
        self,
        coordinator: GrundigCoordinator,
        entry: ConfigEntry,
        tv_info: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, entry, tv_info)
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_source"

    async def async_select_option(self, option: str) -> None:
        """Switch to the selected HDMI input."""
        input_number = HDMI_INPUTS.get(option)
        if input_number is None:
            raise HomeAssistantError(f"Unknown source {option!r}.")

        try:
            await self.coordinator.api.async_open_hdmi(input_number)
        except GrundigError as err:
            raise HomeAssistantError(
                f"Could not switch to {option}."
            ) from err

        self._attr_current_option = option
        self.async_write_ha_state()


class GrundigChannelSelect(GrundigEntity, SelectEntity):
    """Select the current broadcast channel."""

    _attr_name = "Channel"
    _attr_icon = "mdi:television-guide"

    def __init__(
        self,
        coordinator: GrundigCoordinator,
        entry: ConfigEntry,
        tv_info: dict[str, Any],
    ) -> None:
        super().__init__(coordinator, entry, tv_info)
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_channel"
        self._attr_options: list[str] = []
        self._attr_current_option: str | None = None
        self._channels: list[dict[str, Any]] = []
        self._channels_loaded = False
        self._loading = False

    async def async_added_to_hass(self) -> None:
        """Load the channel list once the entity is added."""
        await super().async_added_to_hass()
        await self._async_load_channels()

    @staticmethod
    def _format_channel(channel: dict[str, Any]) -> str:
        """Build a unique, readable option label."""
        number = channel.get("channelNumber", "?")
        name = channel.get("name") or "Unknown"
        service = channel.get("serviceType") or "DTV"
        return f"{number} · {name} ({service})"

    async def _async_load_channels(self) -> None:
        """Fetch the channel list from the TV."""
        if self._loading:
            return
        if not (self.coordinator.data or {}).get("reachable"):
            return

        self._loading = True
        try:
            channels = await self.coordinator.api.async_get_channel_list()
        except GrundigError:
            return
        finally:
            self._loading = False

        self._channels = channels
        self._channels_loaded = True
        self._attr_options = [
            self._format_channel(channel) for channel in channels
        ]
        self._update_current_option()
        self.async_write_ha_state()

    def _update_current_option(self) -> None:
        """Match the TV's current channel to an option label."""
        channel = (self.coordinator.data or {}).get("channel") or {}
        if not channel.get("name"):
            self._attr_current_option = None
            return

        label = self._format_channel(channel)
        self._attr_current_option = (
            label if label in self._attr_options else None
        )

    def _handle_coordinator_update(self) -> None:
        """Reload channels after the TV comes back online."""
        if not self._channels_loaded and (self.coordinator.data or {}).get("reachable"):
            self.hass.async_create_task(self._async_load_channels())
        else:
            self._update_current_option()
        super()._handle_coordinator_update()

    async def async_select_option(self, option: str) -> None:
        """Switch to the selected channel."""
        channel = next(
            (
                channel
                for channel in self._channels
                if self._format_channel(channel) == option
            ),
            None,
        )
        if channel is None:
            raise HomeAssistantError(f"Unknown channel {option!r}.")

        number = channel.get("channelNumber")
        if number is None:
            raise HomeAssistantError(f"Channel {option!r} has no number.")

        try:
            await self.coordinator.api.async_set_channel(
                int(number),
                channel.get("serviceType") or "DTV",
            )
        except GrundigError as err:
            raise HomeAssistantError(
                f"Could not switch to {option}."
            ) from err

        self._attr_current_option = option
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
