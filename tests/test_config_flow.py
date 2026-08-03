"""Tests for the ChargeWindow config flow."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.chargewindow.const import (
    CONF_AREA,
    CONF_BASE_URL,
    CONF_CURRENCY,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)

from .const import API_URL, BASE_URL, STATE_PAYLOAD

USER_INPUT = {
    CONF_BASE_URL: BASE_URL,
    CONF_AREA: "DK2",
    CONF_CURRENCY: "DKK",
    CONF_SCAN_INTERVAL: 15,
}


async def test_user_flow_creates_entry(hass, aioclient_mock) -> None:
    """A successful probe creates a uniquely identified config entry."""
    aioclient_mock.get(API_URL, json=STATE_PAYLOAD)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ChargeWindow (DK2)"
    assert result["data"] == USER_INPUT


async def test_user_flow_reports_connection_error(hass, aioclient_mock) -> None:
    """A failed API probe stays in the form with a friendly error."""
    aioclient_mock.get(API_URL, status=503, text="price data unavailable")

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_rejects_invalid_base_url(hass) -> None:
    """Only absolute HTTP(S) endpoints are accepted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={**USER_INPUT, CONF_BASE_URL: "chargewindow.test"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
