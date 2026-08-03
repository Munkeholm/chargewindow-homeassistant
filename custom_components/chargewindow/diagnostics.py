"""Diagnostics support for ChargeWindow."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data

from . import ChargeWindowConfigEntry
from .const import CONF_BASE_URL


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ChargeWindowConfigEntry
) -> dict[str, Any]:
    """Return safe diagnostics for a public, anonymous integration."""
    coordinator = entry.runtime_data
    data = coordinator.data
    return {
        "entry": {
            "title": entry.title,
            "data": async_redact_data(entry.data, {CONF_BASE_URL}),
            "options": dict(entry.options),
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "area": coordinator.area,
            "requested_currency": coordinator.currency,
            "effective_currency": data.currency,
            "generated_at_utc": (
                data.generated_at_utc.isoformat() if data.generated_at_utc else None
            ),
            "hour_count": len(data.hours),
            "has_current_price": data.current_price is not None,
            "has_cheapest_window": data.cheapest_window_start is not None,
            "has_co2_intensity": data.co2_intensity is not None,
        },
    }
