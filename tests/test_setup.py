"""Integration setup tests for ChargeWindow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.chargewindow.const import (
    CONF_AREA,
    CONF_BASE_URL,
    CONF_CURRENCY,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)

from .const import API_URL, BASE_URL, STATE_PAYLOAD


async def test_setup_creates_typed_entities(hass, aioclient_mock) -> None:
    """One API request populates all sensor platforms."""
    aioclient_mock.get(API_URL, json=STATE_PAYLOAD)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ChargeWindow (DK2)",
        unique_id=f"{BASE_URL}::DK2",
        version=2,
        data={
            CONF_BASE_URL: BASE_URL,
            CONF_AREA: "DK2",
            CONF_CURRENCY: "DKK",
            CONF_SCAN_INTERVAL: 15,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.chargewindow._async_register_frontend",
        new=AsyncMock(),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    current = hass.states.get("sensor.chargewindow_dk2_current_price")
    recommendation = hass.states.get(
        "binary_sensor.chargewindow_dk2_next_hour_is_in_cheapest_window"
    )
    assert current is not None
    assert current.state == "1.25"
    assert current.attributes["currency"] == "DKK"
    assert len(current.attributes["hours"]) == 2
    assert recommendation is not None
    assert recommendation.state == "on"
