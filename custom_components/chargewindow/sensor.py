"""Sensor platform for ChargeWindow."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from . import ChargeWindowConfigEntry
from .coordinator import ChargeWindowCoordinator
from .entity import ChargeWindowEntity

_LOGGER = logging.getLogger(__name__)


def _get(data: dict[str, Any], *path: str) -> Any:
    """Safely walk a nested dict; return None if any key missing/None."""
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
        if cur is None:
            return None
    return cur


def _parse_dt(value: Any) -> datetime | None:
    """Parse an ISO date-time string into a tz-aware datetime."""
    if not value or not isinstance(value, str):
        return None
    parsed = dt_util.parse_datetime(value)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        # Local datetimes from the API are in the area's local time; assume HA local.
        parsed = dt_util.as_local(parsed)
    return parsed


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChargeWindowConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ChargeWindow sensors."""
    coordinator = entry.runtime_data
    currency = coordinator.currency

    entities: list[SensorEntity] = [
        CurrentPriceSensor(coordinator, currency),
        SpotPriceSensor(coordinator, currency),
        CheapestWindowStartSensor(coordinator),
        CheapestWindowEndSensor(coordinator),
        CheapestWindowAvgPriceSensor(coordinator, currency),
        SavingsVsNowSensor(coordinator, currency),
        Co2IntensitySensor(coordinator),
    ]
    async_add_entities(entities)


class CurrentPriceSensor(ChargeWindowEntity, SensorEntity):
    """All-in current price; carries the full hours series as attributes."""

    _attr_translation_key = "current_price"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(
        self, coordinator: ChargeWindowCoordinator, currency: str
    ) -> None:
        super().__init__(coordinator, "current_price")
        self._attr_native_unit_of_measurement = f"{currency}/kWh"

    @property
    def native_value(self) -> float | None:
        return _get(self._data, "currentPrice", "allInDkkPerKWh")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self._data
        return {
            "area": data.get("area"),
            "currency": data.get("currency"),
            "generated_at_utc": data.get("generatedAtUtc"),
            "is_cheap_now": data.get("isCheapNow"),
            "hours": data.get("hours") or [],
        }


class SpotPriceSensor(ChargeWindowEntity, SensorEntity):
    """Spot-only current price."""

    _attr_translation_key = "spot_price"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(
        self, coordinator: ChargeWindowCoordinator, currency: str
    ) -> None:
        super().__init__(coordinator, "spot_price")
        self._attr_native_unit_of_measurement = f"{currency}/kWh"

    @property
    def native_value(self) -> float | None:
        return _get(self._data, "currentPrice", "spotOnly")


class CheapestWindowStartSensor(ChargeWindowEntity, SensorEntity):
    """Start of the cheapest charging window."""

    _attr_translation_key = "cheapest_window_start"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "cheapest_window_start")

    @property
    def native_value(self) -> datetime | None:
        return _parse_dt(_get(self._data, "cheapestWindow", "startLocal"))


class CheapestWindowEndSensor(ChargeWindowEntity, SensorEntity):
    """End of the cheapest charging window."""

    _attr_translation_key = "cheapest_window_end"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "cheapest_window_end")

    @property
    def native_value(self) -> datetime | None:
        return _parse_dt(_get(self._data, "cheapestWindow", "endLocal"))


class CheapestWindowAvgPriceSensor(ChargeWindowEntity, SensorEntity):
    """Average price across the cheapest window."""

    _attr_translation_key = "cheapest_window_avg_price"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(
        self, coordinator: ChargeWindowCoordinator, currency: str
    ) -> None:
        super().__init__(coordinator, "cheapest_window_avg_price")
        self._attr_native_unit_of_measurement = f"{currency}/kWh"

    @property
    def native_value(self) -> float | None:
        return _get(self._data, "cheapestWindow", "avgPrice")


class SavingsVsNowSensor(ChargeWindowEntity, SensorEntity):
    """Absolute savings vs charging now (percent in attributes)."""

    _attr_translation_key = "savings_vs_now"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(
        self, coordinator: ChargeWindowCoordinator, currency: str
    ) -> None:
        super().__init__(coordinator, "savings_vs_now")
        self._attr_native_unit_of_measurement = f"{currency}/kWh"

    @property
    def native_value(self) -> float | None:
        return _get(self._data, "savingsVsChargingNow", "absolute")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"percent": _get(self._data, "savingsVsChargingNow", "percent")}


class Co2IntensitySensor(ChargeWindowEntity, SensorEntity):
    """Current grid CO2 intensity."""

    _attr_translation_key = "co2_intensity"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "gCO2/kWh"
    _attr_icon = "mdi:molecule-co2"

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "co2_intensity")

    @property
    def native_value(self) -> float | None:
        return self._data.get("co2IntensityNow")

    @property
    def available(self) -> bool:
        return super().available and self._data.get("co2IntensityNow") is not None
