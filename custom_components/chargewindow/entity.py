"""Base entity for ChargeWindow."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChargeWindowCoordinator


class ChargeWindowEntity(CoordinatorEntity[ChargeWindowCoordinator]):
    """Base entity that ties all ChargeWindow entities to one device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ChargeWindowCoordinator, key: str) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._key = key
        entry = coordinator.config_entry
        stable_entry_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{stable_entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, stable_entry_id)},
            name=f"ChargeWindow ({coordinator.area})",
            manufacturer="ChargeWindow",
            model="Price optimizer",
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=coordinator.url,
        )
