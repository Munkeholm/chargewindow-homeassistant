"""The ChargeWindow integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_AREA,
    CONF_BASE_URL,
    CONF_CURRENCY,
    CONF_SCAN_INTERVAL,
    DEFAULT_AREA,
    DEFAULT_BASE_URL,
    DEFAULT_CURRENCY,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
)
from .coordinator import ChargeWindowCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type ChargeWindowConfigEntry = ConfigEntry[ChargeWindowCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: ChargeWindowConfigEntry
) -> bool:
    """Set up ChargeWindow from a config entry."""
    scan_interval_minutes = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES),
    )

    coordinator = ChargeWindowCoordinator(
        hass,
        base_url=entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL),
        area=entry.data.get(CONF_AREA, DEFAULT_AREA),
        currency=entry.data.get(CONF_CURRENCY, DEFAULT_CURRENCY),
        scan_interval=timedelta(minutes=scan_interval_minutes),
    )

    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ChargeWindowConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(
    hass: HomeAssistant, entry: ChargeWindowConfigEntry
) -> None:
    """Reload the entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
