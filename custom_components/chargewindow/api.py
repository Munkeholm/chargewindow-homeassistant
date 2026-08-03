"""Async client and typed response model for the ChargeWindow API."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import aiohttp
from homeassistant.util import dt as dt_util

from .const import API_PATH, REQUEST_TIMEOUT

_MARKET_TIME_ZONE = dt_util.get_time_zone("Europe/Copenhagen")


class ChargeWindowApiError(Exception):
    """Base error raised by the ChargeWindow API client."""


class ChargeWindowConnectionError(ChargeWindowApiError):
    """Raised when the ChargeWindow API cannot be reached."""


class ChargeWindowResponseError(ChargeWindowApiError):
    """Raised when the ChargeWindow API returns an invalid response."""


def _number(value: Any) -> float | None:
    """Return a finite numeric value without accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if result == result and abs(result) != float("inf") else None


def _parse_datetime(value: Any) -> datetime | None:
    """Parse API datetimes and attach the Nordic market timezone when omitted."""
    if not isinstance(value, str) or not value:
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None and _MARKET_TIME_ZONE is not None:
        parsed = parsed.replace(tzinfo=_MARKET_TIME_ZONE)
    return parsed


@dataclass(frozen=True, slots=True)
class ChargeWindowHour:
    """One hourly price point."""

    hour_local: datetime
    price_all_in: float
    is_past: bool
    is_cheap: bool

    @classmethod
    def from_payload(cls, payload: Any) -> ChargeWindowHour | None:
        """Create an hour from an API object, or skip an invalid row."""
        if not isinstance(payload, dict):
            return None
        hour_local = _parse_datetime(payload.get("hourLocal"))
        price_all_in = _number(payload.get("priceAllIn"))
        if hour_local is None or price_all_in is None:
            return None
        return cls(
            hour_local=hour_local,
            price_all_in=price_all_in,
            is_past=payload.get("isPast") is True,
            is_cheap=payload.get("isCheap") is True,
        )


@dataclass(frozen=True, slots=True)
class ChargeWindowData:
    """Validated state consumed by all ChargeWindow entities."""

    area: str | None
    currency: str | None
    requested_currency: str | None
    current_price: float | None
    spot_price: float | None
    next_hour_is_cheap: bool | None
    cheapest_window_start: datetime | None
    cheapest_window_end: datetime | None
    cheapest_window_avg_price: float | None
    savings_absolute: float | None
    savings_percent: float | None
    co2_intensity: float | None
    hours: tuple[ChargeWindowHour, ...]
    generated_at_utc: datetime | None = field(compare=False)

    @classmethod
    def from_payload(cls, payload: Any) -> ChargeWindowData:
        """Validate and normalize a ChargeWindow response."""
        if not isinstance(payload, dict):
            raise ChargeWindowResponseError("Unexpected response payload")

        current = payload.get("currentPrice")
        window = payload.get("cheapestWindow")
        savings = payload.get("savingsVsChargingNow")
        current = current if isinstance(current, dict) else {}
        window = window if isinstance(window, dict) else {}
        savings = savings if isinstance(savings, dict) else {}

        hours_payload = payload.get("hours")
        if not isinstance(hours_payload, list):
            hours_payload = []
        parsed_hours = (ChargeWindowHour.from_payload(item) for item in hours_payload)
        next_hour = payload.get("isNextHourInCheapestWindow", payload.get("isCheapNow"))

        return cls(
            area=payload.get("area") if isinstance(payload.get("area"), str) else None,
            currency=(
                payload.get("currency")
                if isinstance(payload.get("currency"), str)
                else None
            ),
            requested_currency=(
                payload.get("requestedCurrency")
                if isinstance(payload.get("requestedCurrency"), str)
                else None
            ),
            generated_at_utc=_parse_datetime(payload.get("generatedAtUtc")),
            current_price=_number(
                current.get("allInPerKWh", current.get("allInDkkPerKWh"))
            ),
            spot_price=_number(current.get("spotOnly")),
            next_hour_is_cheap=next_hour if isinstance(next_hour, bool) else None,
            cheapest_window_start=_parse_datetime(window.get("startLocal")),
            cheapest_window_end=_parse_datetime(window.get("endLocal")),
            cheapest_window_avg_price=_number(window.get("avgPrice")),
            savings_absolute=_number(savings.get("absolute")),
            savings_percent=_number(savings.get("percent")),
            co2_intensity=_number(payload.get("co2IntensityNow")),
            hours=tuple(hour for hour in parsed_hours if hour is not None),
        )

    def card_attributes(self) -> dict[str, Any]:
        """Return normalized attributes consumed by the bundled dashboard card."""
        return {
            "area": self.area,
            "currency": self.currency,
            "requested_currency": self.requested_currency,
            "generated_at_utc": (
                self.generated_at_utc.isoformat() if self.generated_at_utc else None
            ),
            "next_hour_is_cheap": self.next_hour_is_cheap,
            "savings_vs_now_percent": self.savings_percent,
            "savings_vs_now_absolute": self.savings_absolute,
            "co2_intensity": self.co2_intensity,
            "cheapest_window_start": (
                self.cheapest_window_start.isoformat()
                if self.cheapest_window_start
                else None
            ),
            "cheapest_window_end": (
                self.cheapest_window_end.isoformat()
                if self.cheapest_window_end
                else None
            ),
            "cheapest_window_avg_price": self.cheapest_window_avg_price,
            "hours": [
                {
                    "hourLocal": hour.hour_local.isoformat(),
                    "priceAllIn": hour.price_all_in,
                    "isPast": hour.is_past,
                    "isCheap": hour.is_cheap,
                }
                for hour in self.hours
            ],
        }


class ChargeWindowApiClient:
    """Small async client shared by config flow and update coordinator."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        *,
        base_url: str,
        area: str,
        currency: str,
    ) -> None:
        self._session = session
        self._url = f"{base_url.rstrip('/')}{API_PATH}"
        self._params = {"area": area, "currency": currency}

    async def async_get_state(self) -> ChargeWindowData:
        """Fetch and validate the latest ChargeWindow state."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                async with self._session.get(
                    self._url, params=self._params
                ) as response:
                    if response.status != 200:
                        detail = (await response.text())[:200]
                        raise ChargeWindowConnectionError(
                            "ChargeWindow API returned "
                            f"HTTP {response.status}: {detail}"
                        )
                    payload = await response.json()
        except TimeoutError as err:
            raise ChargeWindowConnectionError(
                "Timeout while contacting ChargeWindow API"
            ) from err
        except (aiohttp.ClientError, ValueError) as err:
            raise ChargeWindowConnectionError(
                f"Error contacting ChargeWindow API: {err}"
            ) from err

        return ChargeWindowData.from_payload(payload)
