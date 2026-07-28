"""Hub availability entities for Domee."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DomeeRuntimeData
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[DomeeRuntimeData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add Domee hub availability sensors."""
    runtime = entry.runtime_data
    known: set[str] = set()

    def add_new_entities() -> None:
        entities = []
        for hub in runtime.coordinator.data.hubs:
            unique_id = f"{hub.identifier}_availability"
            if unique_id in known:
                continue
            known.add(unique_id)
            entities.append(DomeeHubAvailability(runtime, hub.id))
        if entities:
            async_add_entities(entities)

    add_new_entities()
    entry.async_on_unload(runtime.coordinator.async_add_listener(add_new_entities))


class DomeeHubAvailability(
    CoordinatorEntity,
    BinarySensorEntity,
):
    """Connectivity state reported by the Domee server."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, runtime: DomeeRuntimeData, hub_id: str) -> None:
        super().__init__(runtime.coordinator)
        self._hub_id = hub_id
        self._attr_unique_id = f"domee_hub_{hub_id}_availability"

    @property
    def _hub(self):
        return self.coordinator.data.hub_by_id(self._hub_id)

    @property
    def is_on(self) -> bool:
        return bool(self._hub and self._hub.available)

    @property
    def available(self) -> bool:
        return super().available and self._hub is not None

    @property
    def device_info(self) -> DeviceInfo:
        hub = self._hub
        if hub is None:
            return DeviceInfo(
                identifiers={(DOMAIN, f"domee_hub_{self._hub_id}")},
                name="Domee Hub",
            )
        return DeviceInfo(
            identifiers={(DOMAIN, hub.identifier)},
            name=hub.diagnostics.hostname or hub.name,
            model=hub.model,
            manufacturer=hub.manufacturer,
            sw_version=hub.firmware_version,
        )
