"""The ChargeWindow integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

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

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

# Public URL the bundled Lovelace card is served at, and the flag key used to
# ensure we only register the static path + frontend module once per HA run.
CARD_FILENAME = "chargewindow-card.js"
CARD_URL_PATH = f"/{DOMAIN}/{CARD_FILENAME}"
FRONTEND_REGISTERED_FLAG = f"{DOMAIN}_frontend_registered"

type ChargeWindowConfigEntry = ConfigEntry[ChargeWindowCoordinator]


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Serve and auto-load the bundled Lovelace card exactly once.

    Registers a static HTTP path for the bundled card and adds it as an extra
    frontend JS module so users do not need to add a dashboard resource
    manually. Guarded by a hass.data flag so repeated config-entry setups /
    reloads do not double-register.
    """
    if hass.data.get(FRONTEND_REGISTERED_FLAG):
        return
    hass.data[FRONTEND_REGISTERED_FLAG] = True

    card_path = Path(__file__).parent / "www" / CARD_FILENAME

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                CARD_URL_PATH,
                str(card_path),
                cache_headers=False,
            )
        ]
    )

    # Cache-bust with the integration version so updates load after upgrades.
    version = "0"
    try:
        integration = await async_get_integration(hass, DOMAIN)
        version = integration.version or "0"
    except Exception:  # noqa: BLE001 - version is best-effort only
        _LOGGER.debug("Could not resolve integration version for cache-busting")

    add_extra_js_url(hass, f"{CARD_URL_PATH}?v={version}")
    _LOGGER.debug("Registered ChargeWindow card at %s", CARD_URL_PATH)


async def async_setup_entry(
    hass: HomeAssistant, entry: ChargeWindowConfigEntry
) -> bool:
    """Set up ChargeWindow from a config entry."""
    await _async_register_frontend(hass)

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
