"""Sensor platform for ChargeWindow."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ChargeWindowConfigEntry
from .coordinator import ChargeWindowCoordinator
from .entity import ChargeWindowEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChargeWindowConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up ChargeWindow sensors."""
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        CurrentPriceSensor(coordinator),
        SpotPriceSensor(coordinator),
        CheapestWindowStartSensor(coordinator),
        CheapestWindowEndSensor(coordinator),
        CheapestWindowAvgPriceSensor(coordinator),
        SavingsVsNowSensor(coordinator),
        Co2IntensitySensor(coordinator),
    ]
    async_add_entities(entities)


class CurrentPriceSensor(ChargeWindowEntity, SensorEntity):
    """All-in current price; carries the full hours series as attributes."""

    _attr_translation_key = "current_price"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3
    _unrecorded_attributes = frozenset(
        {
            "hours",
            "generated_at_utc",
            "requested_currency",
            "cheapest_window_start",
            "cheapest_window_end",
            "cheapest_window_avg_price",
            "savings_vs_now_percent",
            "savings_vs_now_absolute",
            "co2_intensity",
        }
    )

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "current_price")

    @property
    def native_unit_of_measurement(self) -> str | None:
        currency = self.coordinator.data.currency
        return f"{currency}/kWh" if currency else None

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.current_price

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return self.coordinator.data.card_attributes()


class SpotPriceSensor(ChargeWindowEntity, SensorEntity):
    """Spot-only current price."""

    _attr_translation_key = "spot_price"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "spot_price")

    @property
    def native_unit_of_measurement(self) -> str | None:
        currency = self.coordinator.data.currency
        return f"{currency}/kWh" if currency else None

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.spot_price


class CheapestWindowStartSensor(ChargeWindowEntity, SensorEntity):
    """Start of the cheapest charging window."""

    _attr_translation_key = "cheapest_window_start"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "cheapest_window_start")

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.cheapest_window_start


class CheapestWindowEndSensor(ChargeWindowEntity, SensorEntity):
    """End of the cheapest charging window."""

    _attr_translation_key = "cheapest_window_end"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "cheapest_window_end")

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.data.cheapest_window_end


class CheapestWindowAvgPriceSensor(ChargeWindowEntity, SensorEntity):
    """Average price across the cheapest window."""

    _attr_translation_key = "cheapest_window_avg_price"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "cheapest_window_avg_price")

    @property
    def native_unit_of_measurement(self) -> str | None:
        currency = self.coordinator.data.currency
        return f"{currency}/kWh" if currency else None

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.cheapest_window_avg_price


class SavingsVsNowSensor(ChargeWindowEntity, SensorEntity):
    """Absolute savings vs charging now (percent in attributes)."""

    _attr_translation_key = "savings_vs_now"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 3

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "savings_vs_now")

    @property
    def native_unit_of_measurement(self) -> str | None:
        return self.coordinator.data.currency

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.savings_absolute

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"percent": self.coordinator.data.savings_percent}


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
        return self.coordinator.data.co2_intensity

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.data.co2_intensity is not None
