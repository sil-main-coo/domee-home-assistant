"""Focused tests for the Domee Wi-Fi switch platform."""

import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

from custom_components.domee.snapshot import (
    DomeeEntitySnapshot,
    DomeeSnapshot,
)
from custom_components.domee.switch import DomeeSwitch, async_setup_entry


def switch_description(power: bool | None = False) -> DomeeEntitySnapshot:
    return DomeeEntitySnapshot(
        unique_id="domee_switch_synthetic-device-1_1",
        platform="switch",
        device_id="synthetic-device-1",
        device_identifier="domee_device_synthetic-device-1",
        channel=1,
        name="Relay 1",
        power=power,
        available=True,
        can_control=True,
    )


def test_setup_adds_switch_once_across_coordinator_updates() -> None:
    asyncio.run(_test_setup_adds_switch_once_across_coordinator_updates())


async def _test_setup_adds_switch_once_across_coordinator_updates() -> None:
    listeners = []
    coordinator = SimpleNamespace(
        data=DomeeSnapshot(
            2,
            "synthetic-account-1",
            (),
            (),
            (
                switch_description(),
                replace(switch_description(), platform="button"),
            ),
        ),
        async_add_listener=lambda listener: listeners.append(listener) or Mock(),
    )
    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(coordinator=coordinator, api=Mock()),
        async_on_unload=Mock(),
    )
    add_entities = Mock()

    with patch(
        "custom_components.domee.switch.DomeeSwitch",
        side_effect=lambda runtime, description: description.unique_id,
    ):
        await async_setup_entry(Mock(), entry, add_entities)
        listeners[0]()

    add_entities.assert_called_once_with(["domee_switch_synthetic-device-1_1"])


def test_switch_reads_initial_reported_state() -> None:
    entity = object.__new__(DomeeSwitch)
    entity.description = switch_description(power=True)
    entity.refresh_description = Mock()

    assert entity.is_on is True
    entity.refresh_description.assert_called_once()


@pytest.mark.parametrize(
    ("physical_available", "expected"),
    [(True, True), (False, False)],
)
def test_switch_maps_physical_availability(
    physical_available: bool, expected: bool
) -> None:
    entity = object.__new__(DomeeSwitch)
    entity.description = switch_description(power=True)
    entity.description = replace(
        entity.description, available=physical_available
    )
    entity.refresh_description = Mock()
    entity._attr_unique_id = entity.description.unique_id
    entity.coordinator = SimpleNamespace(
        last_update_success=True,
        data=DomeeSnapshot(
            2, "synthetic-account-1", (), (), (entity.description,)
        ),
    )

    assert entity.available is expected
    assert entity.is_on is True


@pytest.mark.parametrize(
    ("power", "expected"),
    [(None, None), (False, False), (True, True)],
)
def test_switch_maps_unknown_off_and_on_state(
    power: bool | None, expected: bool | None
) -> None:
    entity = object.__new__(DomeeSwitch)
    entity.description = switch_description()
    entity.description = replace(entity.description, power=power)
    entity.refresh_description = Mock()

    assert entity.is_on is expected


@pytest.mark.parametrize(
    ("method", "value"),
    [("async_turn_on", True), ("async_turn_off", False)],
)
def test_switch_command_and_coordinator_refresh(
    method: str, value: bool
) -> None:
    asyncio.run(_test_switch_command_and_coordinator_refresh(method, value))


async def _test_switch_command_and_coordinator_refresh(
    method: str, value: bool
) -> None:
    entity = object.__new__(DomeeSwitch)
    entity.description = switch_description()
    entity.refresh_description = Mock()
    entity._api = SimpleNamespace(async_set_switch_power=AsyncMock())
    entity.coordinator = SimpleNamespace(async_request_refresh=AsyncMock())

    with patch(
        "custom_components.domee.switch.asyncio.sleep", new=AsyncMock()
    ) as sleep:
        await getattr(entity, method)()

    entity._api.async_set_switch_power.assert_awaited_once_with(
        "synthetic-device-1", 1, value
    )
    sleep.assert_awaited_once_with(0.5)
    entity.coordinator.async_request_refresh.assert_awaited_once()
