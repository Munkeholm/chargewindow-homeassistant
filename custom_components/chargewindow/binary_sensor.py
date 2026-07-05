"""Binary sensor platform for ChargeWindow."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up ChargeWindow binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities([IsCheapNowBinarySensor(coordinator)])


class IsCheapNowBinarySensor(ChargeWindowEntity, BinarySensorEntity):
    """True when charging now is currently considered cheap."""

    _attr_translation_key = "is_cheap_now"
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "is_cheap_now")

    @property
    def is_on(self) -> bool | None:
        value = self._data.get("isCheapNow")
        if value is None:
            return None
        return bool(value)

    @property
    def available(self) -> bool:
        return super().available and self._data.get("isCheapNow") is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"generated_at_utc": self._data.get("generatedAtUtc")}
