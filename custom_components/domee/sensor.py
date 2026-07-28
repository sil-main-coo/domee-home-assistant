"""Central hub diagnostic sensors for Domee."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DomeeRuntimeData
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class HubDiagnosticDescription:
    """Description of one normalized hub diagnostic."""

    key: str
    name: str
    device_class: SensorDeviceClass | None = None
    native_unit: str | None = None
    state_class: SensorStateClass | None = None
    enabled_default: bool = True


DESCRIPTIONS = (
    HubDiagnosticDescription(
        key="signalDbm",
        name="Wi-Fi signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    HubDiagnosticDescription(
        key="uptimeSeconds",
        name="Uptime",
        device_class=SensorDeviceClass.DURATION,
        native_unit=UnitOfTime.SECONDS,
    ),
    HubDiagnosticDescription(
        key="supplyVoltage",
        name="Supply voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        enabled_default=False,
    ),
    HubDiagnosticDescription(
        key="ipAddress",
        name="IP address",
        enabled_default=False,
    ),
    HubDiagnosticDescription(
        key="ssid",
        name="SSID",
        enabled_default=False,
    ),
)

_DIAGNOSTIC_ATTRIBUTES = {
    "signalDbm": "signal_dbm",
    "uptimeSeconds": "uptime_seconds",
    "supplyVoltage": "supply_voltage",
    "ipAddress": "ip_address",
    "ssid": "ssid",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[DomeeRuntimeData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add and discover central hub diagnostic sensors."""
    runtime = entry.runtime_data
    known: set[str] = set()

    def add_new_entities() -> None:
        entities = []
        for hub in runtime.coordinator.data.hubs:
            for description in DESCRIPTIONS:
                unique_id = f"{hub.identifier}_{description.key}"
                if unique_id in known:
                    continue
                known.add(unique_id)
                entities.append(
                    DomeeHubDiagnosticSensor(
                        runtime, hub.id, description
                    )
                )
        if entities:
            async_add_entities(entities)

    add_new_entities()
    entry.async_on_unload(runtime.coordinator.async_add_listener(add_new_entities))


class DomeeHubDiagnosticSensor(CoordinatorEntity, SensorEntity):
    """One normalized diagnostic value reported by a central hub."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_has_entity_name = True

    def __init__(
        self,
        runtime: DomeeRuntimeData,
        hub_id: str,
        description: HubDiagnosticDescription,
    ) -> None:
        super().__init__(runtime.coordinator)
        self._hub_id = hub_id
        self._description = description
        self._attr_unique_id = (
            f"domee_hub_{hub_id}_{description.key}"
        )
        self._attr_name = description.name
        self._attr_device_class = description.device_class
        self._attr_native_unit_of_measurement = description.native_unit
        self._attr_state_class = description.state_class
        self._attr_entity_registry_enabled_default = (
            description.enabled_default
        )

    @property
    def _hub(self):
        return self.coordinator.data.hub_by_id(self._hub_id)

    @property
    def native_value(self) -> Any:
        hub = self._hub
        if hub is None:
            return None
        return getattr(hub.diagnostics, _DIAGNOSTIC_ATTRIBUTES[self._description.key])

    @property
    def available(self) -> bool:
        hub = self._hub
        return (
            super().available
            and hub is not None
            and hub.available
        )

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
