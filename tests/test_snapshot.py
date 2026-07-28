"""Tests for the centralized Domee snapshot compatibility contract."""

import pytest

from custom_components.domee.snapshot import (
    DomeeSnapshotError,
    DomeeUnsupportedSnapshotVersionError,
    parse_snapshot,
)


def valid_snapshot(schema_version: int = 2) -> dict:
    return {
        "schemaVersion": schema_version,
        "backendInstanceId": "a0ebcb2a-ef69-4db7-9dca-3dfdcd57364e",
        "account": {"id": "synthetic-account-1"},
        "hubs": [
            {
                "id": "synthetic-hub-1",
                "identifier": "domee_hub_synthetic-hub-1",
                "serial": "synthetic-hub-serial",
                "name": "Living room",
                "available": True,
                "diagnostics": {
                    "hostname": "hub-host",
                    "signalDbm": -71,
                    "uptimeSeconds": 597,
                    "supplyVoltage": 3.357,
                },
            }
        ],
        "devices": [
            {
                "id": "synthetic-device-1",
                "identifier": "domee_device_synthetic-device-1",
                "hubId": "synthetic-hub-1",
                "name": "Switch",
            }
        ],
        "entities": [
            {
                "uniqueId": "domee_button_button-1",
                "platform": "button",
                "actionType": "button",
                "sourceId": "button-1",
                "hubId": "synthetic-hub-1",
                "deviceIdentifier": "domee_hub_synthetic-hub-1",
                "name": "Power",
                "available": True,
                "canControl": True,
            },
            {
                "uniqueId": "domee_switch_synthetic-device-1_1",
                "platform": "switch",
                "deviceId": "synthetic-device-1",
                "deviceIdentifier": "domee_device_synthetic-device-1",
                "channel": 1,
                "power": True,
                "available": True,
                "canControl": True,
            },
        ],
    }


@pytest.mark.parametrize("value", [None, [], "snapshot", 1])
def test_non_object_snapshot_is_invalid(value) -> None:
    with pytest.raises(DomeeSnapshotError, match="snapshot must be an object"):
        parse_snapshot(value)


@pytest.mark.parametrize(
    "version",
    [None, "2", 2.0, True],
)
def test_missing_or_wrong_type_schema_version_is_invalid(version) -> None:
    raw = valid_snapshot()
    if version is None:
        raw.pop("schemaVersion")
    else:
        raw["schemaVersion"] = version

    with pytest.raises(DomeeSnapshotError, match="schemaVersion"):
        parse_snapshot(raw)


def test_unsupported_future_schema_version_is_explicit() -> None:
    raw = valid_snapshot()
    raw["schemaVersion"] = 3
    with pytest.raises(
        DomeeUnsupportedSnapshotVersionError,
        match="schemaVersion 3",
    ):
        parse_snapshot(raw)


@pytest.mark.parametrize("field", ["hubs", "devices", "entities"])
def test_malformed_collection_invalidates_entire_snapshot(field: str) -> None:
    raw = valid_snapshot()
    raw[field] = {}
    with pytest.raises(DomeeSnapshotError, match=field):
        parse_snapshot(raw)


def test_malformed_nested_device_invalidates_entire_snapshot() -> None:
    raw = valid_snapshot()
    raw["devices"][0] = {"id": "synthetic-device-1", "identifier": []}
    with pytest.raises(DomeeSnapshotError, match=r"devices\[0\].identifier"):
        parse_snapshot(raw)


def test_missing_required_hub_identity_invalidates_entire_snapshot() -> None:
    raw = valid_snapshot()
    raw["hubs"][0].pop("id")
    with pytest.raises(DomeeSnapshotError, match=r"hubs\[0\].id"):
        parse_snapshot(raw)


def test_malformed_diagnostics_normalizes_optional_values_to_none() -> None:
    raw = valid_snapshot()
    raw["hubs"][0]["diagnostics"] = {
        "hostname": 123,
        "ipAddress": [],
        "signalDbm": True,
        "uptimeSeconds": -1,
        "supplyVoltage": "3.3",
    }
    diagnostics = parse_snapshot(raw).hubs[0].diagnostics

    assert diagnostics.hostname is None
    assert diagnostics.ip_address is None
    assert diagnostics.signal_dbm is None
    assert diagnostics.uptime_seconds is None
    assert diagnostics.supply_voltage is None


def test_malformed_switch_channel_drops_only_that_entity() -> None:
    raw = valid_snapshot()
    raw["entities"][1]["channel"] = "1"
    snapshot = parse_snapshot(raw)

    assert [entity.unique_id for entity in snapshot.entities] == [
        "domee_button_button-1"
    ]


def test_malformed_optional_entity_does_not_break_valid_entities() -> None:
    raw = valid_snapshot()
    raw["entities"].insert(0, {"platform": "button", "uniqueId": None})
    snapshot = parse_snapshot(raw)

    assert len(snapshot.entities) == 2


def test_unknown_additive_fields_and_platforms_are_ignored() -> None:
    raw = valid_snapshot()
    raw["futureTopLevel"] = {"raw": "ignored"}
    raw["hubs"][0]["futureHubField"] = ["ignored"]
    raw["entities"].append(
        {
            "uniqueId": "future-1",
            "platform": "light",
            "deviceIdentifier": "domee_device_synthetic-device-1",
            "rawPayload": {"ignored": True},
        }
    )
    snapshot = parse_snapshot(raw)

    assert snapshot.schema_version == 2
    assert len(snapshot.hubs) == 1
    assert len(snapshot.entities) == 2


def test_schema_v1_normalizes_missing_phase2_collections_and_fields() -> None:
    raw = valid_snapshot(1)
    raw.pop("devices")
    raw["hubs"][0].pop("diagnostics")
    raw["entities"] = [raw["entities"][0]]
    snapshot = parse_snapshot(raw)

    assert snapshot.schema_version == 1
    assert snapshot.devices == ()
    assert snapshot.hubs[0].diagnostics.signal_dbm is None
    assert snapshot.entities[0].platform == "button"


def test_schema_v2_preserves_switch_and_diagnostics_contract() -> None:
    snapshot = parse_snapshot(valid_snapshot(2))

    switch = snapshot.entities[1]
    assert switch.channel == 1
    assert switch.power is True
    assert snapshot.hubs[0].diagnostics.signal_dbm == -71


def test_backend_instance_id_is_parsed_and_normalized() -> None:
    raw = valid_snapshot()
    raw["backendInstanceId"] = "A0EBCB2A-EF69-4DB7-9DCA-3DFDCD57364E"

    assert (
        parse_snapshot(raw).backend_instance_id
        == "a0ebcb2a-ef69-4db7-9dca-3dfdcd57364e"
    )


def test_general_snapshot_parser_normalizes_missing_backend_instance_id() -> None:
    raw = valid_snapshot()
    raw.pop("backendInstanceId")

    assert parse_snapshot(raw).backend_instance_id is None


@pytest.mark.parametrize(
    "value",
    [
        123,
        "not-a-uuid",
        "00000000-0000-0000-0000-000000000000",
        "a0ebcb2a-ef69-0db7-9dca-3dfdcd57364e",
    ],
)
def test_malformed_backend_instance_id_invalidates_snapshot(value) -> None:
    raw = valid_snapshot()
    raw["backendInstanceId"] = value

    with pytest.raises(DomeeSnapshotError, match="backendInstanceId"):
        parse_snapshot(raw)
