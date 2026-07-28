"""Shared Domee entity behavior."""

from __future__ import annotations

from dataclasses import replace

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import DomeeCoordinator
from .snapshot import DomeeEntitySnapshot


class DomeeEntity(CoordinatorEntity[DomeeCoordinator]):
    """Entity backed by the consolidated Domee snapshot."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DomeeCoordinator,
        description: DomeeEntitySnapshot,
    ) -> None:
        super().__init__(coordinator)
        self.description = description
        self._attr_unique_id = description.unique_id
        self._attr_name = description.name

    @property
    def available(self) -> bool:
        self.refresh_description()
        return (
            super().available
            and self.description.available
            and self.description.can_control
        )

    @property
    def device_info(self) -> DeviceInfo:
        identifier = self.description.device_identifier
        device = self.coordinator.data.registry_item_by_identifier(identifier)
        hostname = getattr(getattr(device, "diagnostics", None), "hostname", None)
        return DeviceInfo(
            identifiers={(DOMAIN, identifier)},
            name=hostname or getattr(device, "name", "Domee"),
            model=getattr(device, "model", None),
            manufacturer=getattr(device, "manufacturer", "Domee"),
            sw_version=getattr(device, "firmware_version", None),
        )

    def refresh_description(self) -> None:
        """Refresh mutable fields from the latest snapshot."""
        entity = self.coordinator.data.entity_by_unique_id(self._attr_unique_id)
        if entity is not None:
            self.description = entity
        else:
            self.description = replace(self.description, available=False)
