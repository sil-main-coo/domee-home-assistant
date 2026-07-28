"""Tests for the stable Domee config-entry identity contract."""

import pytest

from custom_components.domee.identity import (
    DomeeIdentityError,
    DomeeMissingInstanceIdError,
    build_config_entry_unique_id,
)

INSTANCE_A = "a0ebcb2a-ef69-4db7-9dca-3dfdcd57364e"
INSTANCE_B = "588b8e81-fbd8-4bd4-8425-201b85ea7155"


def test_identity_uses_only_backend_instance_and_account() -> None:
    assert build_config_entry_unique_id(INSTANCE_A, "synthetic-account-1") == (
        f"domee:{INSTANCE_A}:synthetic-account-1"
    )


def test_identity_distinguishes_installations_and_accounts() -> None:
    identity = build_config_entry_unique_id(INSTANCE_A, "synthetic-account-1")

    assert build_config_entry_unique_id(INSTANCE_B, "synthetic-account-1") != identity
    assert build_config_entry_unique_id(INSTANCE_A, "account-2") != identity


def test_identity_normalizes_uuid_and_rejects_invalid_inputs() -> None:
    assert build_config_entry_unique_id(INSTANCE_A.upper(), " synthetic-account-1 ") == (
        f"domee:{INSTANCE_A}:synthetic-account-1"
    )
    with pytest.raises(DomeeMissingInstanceIdError):
        build_config_entry_unique_id(None, "synthetic-account-1")
    with pytest.raises(DomeeIdentityError):
        build_config_entry_unique_id("not-a-uuid", "synthetic-account-1")
    with pytest.raises(DomeeIdentityError):
        build_config_entry_unique_id(INSTANCE_A, "")
