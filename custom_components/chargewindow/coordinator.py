"""DataUpdateCoordinator for ChargeWindow."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ChargeWindowApiClient, ChargeWindowApiError, ChargeWindowData
from .const import API_PATH, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ChargeWindowCoordinator(DataUpdateCoordinator[ChargeWindowData]):
    """Coordinator that polls the ChargeWindow Home Assistant state endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
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
            config_entry=config_entry,
            update_interval=scan_interval,
            always_update=False,
        )
        self._base_url = base_url.rstrip("/")
        self._area = area
        self._currency = currency
        self._client = ChargeWindowApiClient(
            async_get_clientsession(hass),
            base_url=self._base_url,
            area=area,
            currency=currency,
        )

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

    async def _async_update_data(self) -> ChargeWindowData:
        """Fetch the latest state from the ChargeWindow API."""
        try:
            return await self._client.async_get_state()
        except ChargeWindowApiError as err:
            raise UpdateFailed(str(err)) from err
