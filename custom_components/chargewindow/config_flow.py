"""Config flow for the ChargeWindow integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    API_PATH,
    CONF_AREA,
    CONF_BASE_URL,
    CONF_CURRENCY,
    CONF_SCAN_INTERVAL,
    DEFAULT_AREA,
    DEFAULT_BASE_URL,
    DEFAULT_CURRENCY,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
    REQUEST_TIMEOUT,
    SUPPORTED_AREAS,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_connection(
    hass, base_url: str, area: str, currency: str
) -> None:
    """Make one test call to the endpoint; raise on failure."""
    session = async_get_clientsession(hass)
    url = f"{base_url.rstrip('/')}{API_PATH}"
    params = {"area": area, "currency": currency}
    async with asyncio.timeout(REQUEST_TIMEOUT):
        response = await session.get(url, params=params)
        if response.status != 200:
            raise CannotConnect(f"HTTP {response.status}")
        data = await response.json()
    if not isinstance(data, dict):
        raise CannotConnect("Unexpected payload")


class ChargeWindowConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ChargeWindow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].strip()
            area = user_input[CONF_AREA]
            currency = user_input[CONF_CURRENCY].strip()

            await self.async_set_unique_id(f"{base_url.rstrip('/')}::{area}")
            self._abort_if_unique_id_configured()

            try:
                await _validate_connection(self.hass, base_url, area, currency)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except (aiohttp.ClientError, TimeoutError):
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating ChargeWindow")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"ChargeWindow ({area})",
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_AREA: area,
                        CONF_CURRENCY: currency,
                        CONF_SCAN_INTERVAL: int(
                            user_input[CONF_SCAN_INTERVAL]
                        ),
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_BASE_URL,
                    default=(user_input or {}).get(CONF_BASE_URL, DEFAULT_BASE_URL),
                ): str,
                vol.Required(
                    CONF_AREA,
                    default=(user_input or {}).get(CONF_AREA, DEFAULT_AREA),
                ): SelectSelector(
                    SelectSelectorConfig(
                        options=SUPPORTED_AREAS,
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
                vol.Required(
                    CONF_CURRENCY,
                    default=(user_input or {}).get(CONF_CURRENCY, DEFAULT_CURRENCY),
                ): str,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=(user_input or {}).get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
                    ),
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_MINUTES,
                        max=MAX_SCAN_INTERVAL_MINUTES,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> ChargeWindowOptionsFlow:
        """Return the options flow."""
        return ChargeWindowOptionsFlow()


class ChargeWindowOptionsFlow(OptionsFlow):
    """Handle ChargeWindow options (scan interval)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(
                data={CONF_SCAN_INTERVAL: int(user_input[CONF_SCAN_INTERVAL])}
            )

        current = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
            ),
        )

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL, default=current
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_MINUTES,
                        max=MAX_SCAN_INTERVAL_MINUTES,
                        step=1,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)


class CannotConnect(Exception):
    """Error to indicate we cannot connect."""
