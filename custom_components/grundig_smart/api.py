"""Async client for the Grundig SMART inter@ctive HTTP API."""

from __future__ import annotations

import json
from typing import Any

import aiohttp

from .const import (
    DEFAULT_PORT,
    PATH_CHANNEL,
    PATH_CHANNEL_LIST,
    PATH_SEND_KEY,
    PATH_SET_CHANNEL,
    PATH_TV_INFO,
)


class GrundigError(Exception):
    """Base exception for Grundig API errors."""


class GrundigConnectionError(GrundigError):
    """Raised when the TV cannot be reached."""


class GrundigApiError(GrundigError):
    """Raised when the TV returns an unexpected response."""


class GrundigApi:
    """Small client for the unauthenticated HTTP API on port 8085."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = 10.0,
    ) -> None:
        self._session = session
        self.host = host
        self.port = port
        self._base_url = f"http://{host}:{port}"
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> str:
        """Perform a GET request and return the response body."""
        try:
            async with self._session.get(
                f"{self._base_url}{path}",
                params=params,
                timeout=self._timeout,
            ) as response:
                body = await response.text()
                if response.status != 200:
                    raise GrundigApiError(
                        f"HTTP {response.status} for {path}: {body[:200]}"
                    )
                return body
        except GrundigError:
            raise
        except (TimeoutError, aiohttp.ClientError) as err:
            raise GrundigConnectionError(
                f"Unable to reach {self._base_url}: {err}"
            ) from err

    async def _get_json(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Perform a GET request and decode the JSON response."""
        body = await self._get(path, params)
        try:
            return json.loads(body)
        except ValueError as err:
            raise GrundigApiError(
                f"Invalid JSON from {path}: {body[:200]}"
            ) from err

    async def async_get_tv_info(self) -> dict[str, Any]:
        """Return the tvInfo block from /gettvinfo."""
        data = await self._get_json(PATH_TV_INFO)
        info = data.get("tvInfo") if isinstance(data, dict) else None
        if not isinstance(info, dict):
            raise GrundigApiError("Response does not contain a tvInfo object")
        return info

    async def async_get_channel(self) -> dict[str, Any]:
        """Return the currently selected channel, if any."""
        data = await self._get_json(PATH_CHANNEL)
        channel = data.get("channel") if isinstance(data, dict) else None
        return channel if isinstance(channel, dict) else {}

    async def async_get_channel_list(self) -> list[dict[str, Any]]:
        """Return the channel list from /list."""
        data = await self._get_json(PATH_CHANNEL_LIST)
        channels = data.get("channellist") if isinstance(data, dict) else None
        if not isinstance(channels, list):
            return []
        return [channel for channel in channels if isinstance(channel, dict)]

    async def async_send_key(self, keyid: int, keysymbol: int) -> None:
        """Send a remote-control key."""
        body = await self._get(
            PATH_SEND_KEY,
            {"keyid": keyid, "keysymbol": keysymbol},
        )
        if "set rc key is handled for" not in body.lower():
            raise GrundigApiError(
                f"TV did not acknowledge key {keyid}:{keysymbol}: {body[:200]}"
            )

    async def async_set_channel(
        self,
        channel_number: int,
        service_type: str = "DTV",
    ) -> None:
        """Switch to a channel number."""
        body = await self._get(
            PATH_SET_CHANNEL,
            {"no": channel_number, "service": service_type},
        )
        try:
            data = json.loads(body)
        except ValueError:
            return
        if isinstance(data, dict) and data.get("error"):
            raise GrundigApiError(
                f"TV could not switch to channel {channel_number}: {body[:200]}"
            )
