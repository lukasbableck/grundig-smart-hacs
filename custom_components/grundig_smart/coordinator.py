"""Data coordinator for the Grundig Smart TV integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import GrundigApi, GrundigError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class GrundigCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Poll the TV for its current channel and reachability."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: GrundigApi,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the current channel.

        A connection failure usually means the TV is in standby, so it is
        reported as unreachable instead of failing the whole update.
        """
        try:
            channel = await self.api.async_get_channel()
        except GrundigError as err:
            _LOGGER.debug("TV is not reachable: %s", err)
            return {"reachable": False, "channel": {}}
        return {"reachable": True, "channel": channel}
