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
    async_add_entities([NextHourIsCheapBinarySensor(coordinator)])


class NextHourIsCheapBinarySensor(ChargeWindowEntity, BinarySensorEntity):
    """True when the next whole hour belongs to the cheapest window."""

    _attr_translation_key = "next_hour_is_cheap"
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator: ChargeWindowCoordinator) -> None:
        super().__init__(coordinator, "is_cheap_now")

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.next_hour_is_cheap

    @property
    def available(self) -> bool:
        return (
            super().available and self.coordinator.data.next_hour_is_cheap is not None
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        generated = self.coordinator.data.generated_at_utc
        return {"generated_at_utc": generated.isoformat() if generated else None}
