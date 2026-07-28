"""Stable Home Assistant config-entry identity for Domee."""

from __future__ import annotations

from uuid import RFC_4122, UUID

from .const import DOMAIN


class DomeeIdentityError(ValueError):
    """A snapshot cannot produce a stable Domee config-entry identity."""


class DomeeMissingInstanceIdError(DomeeIdentityError):
    """The backend installation identity is not configured."""


def build_config_entry_unique_id(
    backend_instance_id: str | None,
    account_id: str,
) -> str:
    """Build the URL-independent identity for one backend account."""
    if backend_instance_id is None:
        raise DomeeMissingInstanceIdError(
            "backendInstanceId is required for Domee setup"
        )
    if not isinstance(backend_instance_id, str):
        raise DomeeIdentityError("backendInstanceId must be a UUID string")
    if not backend_instance_id.strip():
        raise DomeeMissingInstanceIdError(
            "backendInstanceId is required for Domee setup"
        )
    if not isinstance(account_id, str) or not account_id.strip():
        raise DomeeIdentityError("accountId must be a non-empty string")

    try:
        instance_id = UUID(backend_instance_id.strip())
    except (ValueError, AttributeError) as error:
        raise DomeeIdentityError(
            "backendInstanceId must be a valid UUID"
        ) from error
    if (
        instance_id.int == 0
        or instance_id.variant != RFC_4122
        or instance_id.version not in range(1, 9)
    ):
        raise DomeeIdentityError("backendInstanceId must be a valid UUID")

    return f"{DOMAIN}:{instance_id}:{account_id.strip()}"
