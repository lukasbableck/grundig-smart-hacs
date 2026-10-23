"""Config flow for the Grundig Smart TV integration."""

from __future__ import annotations

from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import (
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GrundigApi, GrundigApiError, GrundigConnectionError
from .const import (
    CONF_SCAN_INTERVAL,
    CONF_TV_INFO,
    DEFAULT_NAME,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


class GrundigConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for a Grundig TV."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Ask for the TV address and validate it."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            name = (user_input.get(CONF_NAME) or "").strip()

            api = GrundigApi(
                async_get_clientsession(self.hass),
                host,
                port,
            )
            try:
                tv_info = await api.async_get_tv_info()
            except GrundigConnectionError:
                errors["base"] = "cannot_connect"
            except GrundigApiError:
                errors["base"] = "invalid_response"
            else:
                unique_id = str(
                    tv_info.get("macaddress") or f"{host}:{port}"
                ).lower()
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured(
                    updates={CONF_HOST: host, CONF_PORT: port}
                )

                data: dict[str, Any] = {
                    CONF_HOST: host,
                    CONF_PORT: port,
                    CONF_TV_INFO: tv_info,
                }
                if name:
                    data[CONF_NAME] = name

                return self.async_create_entry(
                    title=name or tv_info.get("name") or DEFAULT_NAME,
                    data=data,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): cv.string,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=65535),
                    ),
                    vol.Optional(CONF_NAME): cv.string,
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: Any) -> OptionsFlow:
        """Return the options flow."""
        return GrundigOptionsFlow()


class GrundigOptionsFlow(OptionsFlow):
    """Options for the Grundig integration."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Manage the poll interval."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            DEFAULT_SCAN_INTERVAL,
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_SCAN_INTERVAL,
                            max=MAX_SCAN_INTERVAL,
                        ),
                    )
                }
            ),
        )
