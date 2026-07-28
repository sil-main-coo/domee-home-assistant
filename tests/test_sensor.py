"""Focused tests for central hub diagnostic sensors."""

import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import EntityCategory

from custom_components.domee.sensor import (
    DESCRIPTIONS,
    DomeeHubDiagnosticSensor,
    async_setup_entry,
)
from custom_components.domee.snapshot import (
    DomeeHubDiagnostics,
    DomeeHubSnapshot,
    DomeeSnapshot,
)


def hub(available: bool = True) -> DomeeHubSnapshot:
    return DomeeHubSnapshot(
        id="synthetic-hub-1",
        identifier="domee_hub_synthetic-hub-1",
        serial="synthetic-hub-serial",
        name="Living room",
        model="Domee Box",
        manufacturer="Domee",
        firmware_version="14.0.0.1",
        available=available,
        diagnostics=DomeeHubDiagnostics(
            hostname="synthetic-hub-host",
            ip_address="192.0.2.10",
            ssid="Domee-Test",
            signal_dbm=-71,
            uptime_seconds=597,
            supply_voltage=3.357,
            reported_at="2026-07-26T12:00:00.000Z",
        ),
    )


def make_entity(key: str, available: bool = True) -> DomeeHubDiagnosticSensor:
    entity = object.__new__(DomeeHubDiagnosticSensor)
    entity._hub_id = "synthetic-hub-1"
    entity._description = next(item for item in DESCRIPTIONS if item.key == key)
    entity.coordinator = SimpleNamespace(
        data=DomeeSnapshot(2, "synthetic-account-1", (hub(available),), (), ()),
        last_update_success=True,
    )
    return entity


def test_setup_adds_five_stable_sensors_once() -> None:
    asyncio.run(_test_setup_adds_five_stable_sensors_once())


async def _test_setup_adds_five_stable_sensors_once() -> None:
    listeners = []
    coordinator = SimpleNamespace(
        data=DomeeSnapshot(2, "synthetic-account-1", (hub(),), (), ()),
        async_add_listener=lambda listener: listeners.append(listener) or Mock(),
    )
    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(coordinator=coordinator),
        async_on_unload=Mock(),
    )
    add_entities = Mock()

    with patch(
        "custom_components.domee.sensor.DomeeHubDiagnosticSensor",
        side_effect=lambda runtime, hub_id, description: (
            f"domee_hub_{hub_id}_{description.key}"
        ),
    ):
        await async_setup_entry(Mock(), entry, add_entities)
        listeners[0]()

    add_entities.assert_called_once()
    assert add_entities.call_args.args[0] == [
        "domee_hub_synthetic-hub-1_signalDbm",
        "domee_hub_synthetic-hub-1_uptimeSeconds",
        "domee_hub_synthetic-hub-1_supplyVoltage",
        "domee_hub_synthetic-hub-1_ipAddress",
        "domee_hub_synthetic-hub-1_ssid",
    ]


@pytest.mark.parametrize(
    ("key", "expected"),
    [
        ("signalDbm", -71),
        ("uptimeSeconds", 597),
        ("supplyVoltage", 3.357),
        ("ipAddress", "192.0.2.10"),
        ("ssid", "Domee-Test"),
    ],
)
def test_sensor_reads_normalized_snapshot_value(key: str, expected) -> None:
    assert make_entity(key).native_value == expected


def test_missing_diagnostic_is_unknown_without_fake_state() -> None:
    entity = make_entity("signalDbm")
    empty_hub = replace(
        hub(), diagnostics=replace(hub().diagnostics, signal_dbm=None)
    )
    entity.coordinator.data = DomeeSnapshot(
        2, "synthetic-account-1", (empty_hub,), (), ()
    )
    assert entity.native_value is None


def test_sensor_availability_follows_hub_and_coordinator() -> None:
    entity = make_entity("signalDbm", available=False)
    assert entity.available is False

    entity.coordinator.data = DomeeSnapshot(
        2, "synthetic-account-1", (hub(True),), (), ()
    )
    assert entity.available is True

    entity.coordinator.last_update_success = False
    assert entity.available is False


def test_entity_metadata_and_default_enablement() -> None:
    descriptions = {item.key: item for item in DESCRIPTIONS}
    assert descriptions["signalDbm"].device_class == (
        SensorDeviceClass.SIGNAL_STRENGTH
    )
    assert descriptions["signalDbm"].state_class == SensorStateClass.MEASUREMENT
    assert descriptions["uptimeSeconds"].device_class == (
        SensorDeviceClass.DURATION
    )
    assert descriptions["supplyVoltage"].enabled_default is False
    assert descriptions["ipAddress"].enabled_default is False
    assert descriptions["ssid"].enabled_default is False

    coordinator = SimpleNamespace(
        data=DomeeSnapshot(2, "synthetic-account-1", (hub(),), (), ())
    )
    entity = DomeeHubDiagnosticSensor(
        SimpleNamespace(coordinator=coordinator),
        "synthetic-hub-1",
        descriptions["signalDbm"],
    )
    assert entity._attr_entity_category == EntityCategory.DIAGNOSTIC
    assert entity.unique_id == "domee_hub_synthetic-hub-1_signalDbm"

    voltage = DomeeHubDiagnosticSensor(
        SimpleNamespace(coordinator=coordinator),
        "synthetic-hub-1",
        descriptions["supplyVoltage"],
    )
    assert voltage.entity_registry_enabled_default is False


def test_sensor_device_info_reuses_hub_identity_and_firmware() -> None:
    info = make_entity("signalDbm").device_info
    assert info["identifiers"] == {("domee", "domee_hub_synthetic-hub-1")}
    assert info["name"] == "synthetic-hub-host"
    assert info["manufacturer"] == "Domee"
    assert info["sw_version"] == "14.0.0.1"
