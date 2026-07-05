"""DataUpdateCoordinator for ChargeWindow."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_PATH, DOMAIN, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class ChargeWindowCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls the ChargeWindow Home Assistant state endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        *,
        base_url: str,
        area: str,
        currency: str,
        scan_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{area}",
            update_interval=scan_interval,
        )
        self._base_url = base_url.rstrip("/")
        self._area = area
        self._currency = currency
        self._session = async_get_clientsession(hass)

    @property
    def url(self) -> str:
        """Return the fully-qualified endpoint URL."""
        return f"{self._base_url}{API_PATH}"

    @property
    def area(self) -> str:
        """Return the configured area."""
        return self._area

    @property
    def currency(self) -> str:
        """Return the configured currency."""
        return self._currency

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest state from the ChargeWindow API."""
        params = {"area": self._area, "currency": self._currency}
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(self.url, params=params)
                if response.status != 200:
                    text = await response.text()
                    raise UpdateFailed(
                        f"ChargeWindow API returned HTTP {response.status}: {text[:200]}"
                    )
                data = await response.json()
        except TimeoutError as err:
            raise UpdateFailed("Timeout while contacting ChargeWindow API") from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Error contacting ChargeWindow API: {err}") from err

        if not isinstance(data, dict):
            raise UpdateFailed("Unexpected response payload from ChargeWindow API")

        return data
