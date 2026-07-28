"""Focused tests for Domee hub availability binary sensors."""

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock, patch

from custom_components.domee.binary_sensor import (
    DomeeHubAvailability,
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
            hostname="hub-hostname",
            ip_address=None,
            ssid=None,
            signal_dbm=None,
            uptime_seconds=None,
            supply_voltage=None,
            reported_at=None,
        ),
    )


def make_entity(available: bool = True) -> DomeeHubAvailability:
    coordinator = SimpleNamespace(
        data=DomeeSnapshot(2, "synthetic-account-1", (hub(available),), (), ()),
        last_update_success=True,
    )
    return DomeeHubAvailability(
        SimpleNamespace(coordinator=coordinator),
        "synthetic-hub-1",
    )


def test_setup_adds_stable_availability_entity_once() -> None:
    asyncio.run(_test_setup_adds_stable_availability_entity_once())


async def _test_setup_adds_stable_availability_entity_once() -> None:
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
        "custom_components.domee.binary_sensor.DomeeHubAvailability",
        side_effect=lambda runtime, hub_id: f"domee_hub_{hub_id}_availability",
    ):
        await async_setup_entry(Mock(), entry, add_entities)
        listeners[0]()

    add_entities.assert_called_once_with(["domee_hub_synthetic-hub-1_availability"])
    entry.async_on_unload.assert_called_once()


def test_state_and_availability_follow_normalized_snapshot() -> None:
    entity = make_entity(available=False)
    assert entity.is_on is False
    assert entity.available is True

    entity.coordinator.data = DomeeSnapshot(
        2, "synthetic-account-1", (hub(True),), (), ()
    )
    assert entity.is_on is True

    entity.coordinator.last_update_success = False
    assert entity.available is False


def test_missing_hub_has_unknown_entity_and_stable_identity() -> None:
    entity = make_entity()
    entity.coordinator.data = DomeeSnapshot(2, "synthetic-account-1", (), (), ())

    assert entity.is_on is False
    assert entity.available is False
    assert entity.unique_id == "domee_hub_synthetic-hub-1_availability"
    assert entity.device_info["identifiers"] == {
        ("domee", "domee_hub_synthetic-hub-1")
    }


def test_device_info_uses_stable_hub_identity() -> None:
    entity = make_entity()
    info = entity.device_info

    assert info["identifiers"] == {("domee", "domee_hub_synthetic-hub-1")}
    assert info["name"] == "hub-hostname"
    assert info["manufacturer"] == "Domee"
    assert info["sw_version"] == "14.0.0.1"
