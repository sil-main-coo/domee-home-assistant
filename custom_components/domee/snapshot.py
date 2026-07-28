"""Validated snapshot models for the Domee backend contract."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any
from uuid import RFC_4122, UUID

SUPPORTED_SCHEMA_VERSIONS = frozenset({1, 2})


class DomeeSnapshotError(Exception):
    """The backend returned a malformed snapshot."""


class DomeeUnsupportedSnapshotVersionError(DomeeSnapshotError):
    """The backend snapshot version is not supported."""


@dataclass(frozen=True, slots=True)
class DomeeHubDiagnostics:
    """Normalized optional diagnostics for one central hub."""

    hostname: str | None = None
    ip_address: str | None = None
    ssid: str | None = None
    signal_dbm: int | None = None
    uptime_seconds: int | None = None
    supply_voltage: float | None = None
    reported_at: str | None = None


@dataclass(frozen=True, slots=True)
class DomeeHubSnapshot:
    """Normalized central hub data."""

    id: str
    identifier: str
    serial: str | None
    name: str
    model: str | None
    manufacturer: str
    firmware_version: str | None
    available: bool
    diagnostics: DomeeHubDiagnostics


@dataclass(frozen=True, slots=True)
class DomeeDeviceSnapshot:
    """Normalized child-device registry data."""

    id: str
    identifier: str
    hub_id: str | None
    serial: str | None
    name: str
    model: str | None


@dataclass(frozen=True, slots=True)
class DomeeEntitySnapshot:
    """Normalized button or switch entity description."""

    unique_id: str
    platform: str
    device_identifier: str
    name: str | None
    available: bool
    can_control: bool
    action_type: str | None = None
    source_id: str | None = None
    hub_id: str | None = None
    device_id: str | None = None
    channel: int | None = None
    power: bool | None = None


@dataclass(frozen=True, slots=True)
class DomeeSnapshot:
    """One fully validated and normalized backend snapshot."""

    schema_version: int
    account_id: str
    hubs: tuple[DomeeHubSnapshot, ...]
    devices: tuple[DomeeDeviceSnapshot, ...]
    entities: tuple[DomeeEntitySnapshot, ...]
    backend_instance_id: str | None = None

    def hub_by_id(self, hub_id: str) -> DomeeHubSnapshot | None:
        """Find a hub by its immutable backend ID."""
        return next((hub for hub in self.hubs if hub.id == hub_id), None)

    def registry_item_by_identifier(
        self, identifier: str
    ) -> DomeeHubSnapshot | DomeeDeviceSnapshot | None:
        """Find a hub or child device by its HA registry identifier."""
        return next(
            (
                item
                for item in (*self.devices, *self.hubs)
                if item.identifier == identifier
            ),
            None,
        )

    def entity_by_unique_id(
        self, unique_id: str
    ) -> DomeeEntitySnapshot | None:
        """Find an entity description by stable unique ID."""
        return next(
            (
                entity
                for entity in self.entities
                if entity.unique_id == unique_id
            ),
            None,
        )


def _object(value: Any, path: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DomeeSnapshotError(f"{path} must be an object")
    return value


def _collection(value: Any, path: str) -> list[Any]:
    if not isinstance(value, list):
        raise DomeeSnapshotError(f"{path} must be an array")
    return value


def _required_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomeeSnapshotError(f"{path} must be a non-empty string")
    return value.strip()


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_bool(value: Any, default: bool = False) -> bool:
    return value if isinstance(value, bool) else default


def _parse_backend_instance_id(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DomeeSnapshotError("backendInstanceId must be a UUID string")
    try:
        instance_id = UUID(value.strip())
    except (ValueError, AttributeError) as error:
        raise DomeeSnapshotError(
            "backendInstanceId must be a valid UUID"
        ) from error
    if (
        instance_id.int == 0
        or instance_id.variant != RFC_4122
        or instance_id.version not in range(1, 9)
    ):
        raise DomeeSnapshotError("backendInstanceId must be a valid UUID")
    return str(instance_id)


def _parse_diagnostics(value: Any) -> DomeeHubDiagnostics:
    if not isinstance(value, dict):
        return DomeeHubDiagnostics()

    signal = value.get("signalDbm")
    uptime = value.get("uptimeSeconds")
    voltage = value.get("supplyVoltage")
    return DomeeHubDiagnostics(
        hostname=_optional_string(value.get("hostname")),
        ip_address=_optional_string(value.get("ipAddress")),
        ssid=_optional_string(value.get("ssid")),
        signal_dbm=(
            signal
            if isinstance(signal, int) and not isinstance(signal, bool)
            else None
        ),
        uptime_seconds=(
            uptime
            if isinstance(uptime, int)
            and not isinstance(uptime, bool)
            and uptime >= 0
            else None
        ),
        supply_voltage=(
            float(voltage)
            if isinstance(voltage, int | float)
            and not isinstance(voltage, bool)
            and isfinite(voltage)
            else None
        ),
        reported_at=_optional_string(value.get("reportedAt")),
    )


def _parse_hub(value: Any, index: int) -> DomeeHubSnapshot:
    path = f"hubs[{index}]"
    hub = _object(value, path)
    return DomeeHubSnapshot(
        id=_required_string(hub.get("id"), f"{path}.id"),
        identifier=_required_string(
            hub.get("identifier"), f"{path}.identifier"
        ),
        serial=_optional_string(hub.get("serial")),
        name=_optional_string(hub.get("name")) or "Domee Hub",
        model=_optional_string(hub.get("model")),
        manufacturer=_optional_string(hub.get("manufacturer")) or "Domee",
        firmware_version=_optional_string(hub.get("firmwareVersion")),
        available=_optional_bool(hub.get("available")),
        diagnostics=_parse_diagnostics(hub.get("diagnostics")),
    )


def _parse_device(value: Any, index: int) -> DomeeDeviceSnapshot:
    path = f"devices[{index}]"
    device = _object(value, path)
    return DomeeDeviceSnapshot(
        id=_required_string(device.get("id"), f"{path}.id"),
        identifier=_required_string(
            device.get("identifier"), f"{path}.identifier"
        ),
        hub_id=_optional_string(device.get("hubId")),
        serial=_optional_string(device.get("serial")),
        name=_optional_string(device.get("name")) or "Domee Device",
        model=_optional_string(device.get("model")),
    )


def _parse_entity(value: Any, index: int) -> DomeeEntitySnapshot | None:
    path = f"entities[{index}]"
    entity = _object(value, path)
    platform = _required_string(entity.get("platform"), f"{path}.platform")
    if platform not in {"button", "switch"}:
        return None

    unique_id = _required_string(entity.get("uniqueId"), f"{path}.uniqueId")
    device_identifier = _required_string(
        entity.get("deviceIdentifier"), f"{path}.deviceIdentifier"
    )
    common = {
        "unique_id": unique_id,
        "platform": platform,
        "device_identifier": device_identifier,
        "name": _optional_string(entity.get("name")),
        "available": _optional_bool(entity.get("available")),
        "can_control": _optional_bool(entity.get("canControl")),
    }

    if platform == "button":
        action_type = _required_string(
            entity.get("actionType"), f"{path}.actionType"
        )
        if action_type not in {"button", "script"}:
            raise DomeeSnapshotError(f"{path}.actionType is unsupported")
        hub_id = _required_string(entity.get("hubId"), f"{path}.hubId")
        return DomeeEntitySnapshot(
            **common,
            action_type=action_type,
            source_id=_required_string(
                entity.get("sourceId"), f"{path}.sourceId"
            ),
            hub_id=hub_id,
        )

    channel = entity.get("channel")
    if (
        not isinstance(channel, int)
        or isinstance(channel, bool)
        or channel < 1
    ):
        raise DomeeSnapshotError(
            f"{path}.channel must be a positive integer"
        )
    power = entity.get("power")
    return DomeeEntitySnapshot(
        **common,
        device_id=_required_string(
            entity.get("deviceId"), f"{path}.deviceId"
        ),
        channel=channel,
        power=power if isinstance(power, bool) else None,
    )


def parse_snapshot(value: Any) -> DomeeSnapshot:
    """Validate and normalize a backend snapshot without retaining raw data."""
    snapshot = _object(value, "snapshot")
    version = snapshot.get("schemaVersion")
    if not isinstance(version, int) or isinstance(version, bool):
        raise DomeeSnapshotError("schemaVersion must be an integer")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise DomeeUnsupportedSnapshotVersionError(
            f"Unsupported snapshot schemaVersion {version}"
        )

    account = _object(snapshot.get("account"), "account")
    account_id = _required_string(account.get("id"), "account.id")
    hubs = tuple(
        _parse_hub(item, index)
        for index, item in enumerate(
            _collection(snapshot.get("hubs"), "hubs")
        )
    )
    devices = tuple(
        _parse_device(item, index)
        for index, item in enumerate(
            _collection(snapshot.get("devices", []), "devices")
        )
    )

    entities: list[DomeeEntitySnapshot] = []
    for index, item in enumerate(
        _collection(snapshot.get("entities"), "entities")
    ):
        try:
            entity = _parse_entity(item, index)
        except DomeeSnapshotError:
            continue
        if entity is not None:
            entities.append(entity)

    return DomeeSnapshot(
        schema_version=version,
        account_id=account_id,
        hubs=hubs,
        devices=devices,
        entities=tuple(entities),
        backend_instance_id=_parse_backend_instance_id(
            snapshot.get("backendInstanceId")
        ),
    )
