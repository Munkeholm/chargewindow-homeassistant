"""Base entity for ChargeWindow."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChargeWindowCoordinator


class ChargeWindowEntity(CoordinatorEntity[ChargeWindowCoordinator]):
    """Base entity that ties all ChargeWindow entities to one device."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: ChargeWindowCoordinator, key: str
    ) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"ChargeWindow ({coordinator.area})",
            manufacturer="ChargeWindow",
            model="Price optimizer",
            configuration_url=coordinator.url,
        )

    @property
    def _data(self) -> dict:
        """Return the coordinator data as a dict (never None)."""
        return self.coordinator.data or {}
