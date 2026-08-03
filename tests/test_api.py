"""Tests for the ChargeWindow API response model."""

from __future__ import annotations

import pytest

from custom_components.chargewindow.api import (
    ChargeWindowData,
    ChargeWindowResponseError,
)

from .const import STATE_PAYLOAD


def test_parse_state_payload() -> None:
    """The response is normalized into typed, timezone-aware data."""
    data = ChargeWindowData.from_payload(STATE_PAYLOAD)

    assert data.currency == "DKK"
    assert data.requested_currency == "EUR"
    assert data.current_price == 1.25
    assert data.next_hour_is_cheap is True
    assert data.cheapest_window_start is not None
    assert data.cheapest_window_start.utcoffset() is not None
    assert data.hours[0].price_all_in == -0.15
    assert data.card_attributes()["hours"][1]["isCheap"] is True


def test_legacy_next_hour_field_is_supported() -> None:
    """Existing backends continue to drive the correctly named entity."""
    payload = dict(STATE_PAYLOAD)
    payload.pop("isNextHourInCheapestWindow")
    payload["isCheapNow"] = True

    assert ChargeWindowData.from_payload(payload).next_hour_is_cheap is True


def test_invalid_payload_is_rejected() -> None:
    """Non-object payloads do not reach Home Assistant entities."""
    with pytest.raises(ChargeWindowResponseError):
        ChargeWindowData.from_payload([])


def test_invalid_hour_is_skipped() -> None:
    """One malformed graph point does not take down the integration."""
    payload = dict(STATE_PAYLOAD)
    payload["hours"] = [STATE_PAYLOAD["hours"][0], {"hourLocal": "bad"}]

    assert len(ChargeWindowData.from_payload(payload).hours) == 1
