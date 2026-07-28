"""Focused integration tests for Phase 1 and Phase 2A.1 behavior."""

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.domee import (
    async_setup_entry as async_setup_integration,
)
from custom_components.domee import (
    async_unload_entry as async_unload_integration,
)
from custom_components.domee.api import (
    DomeeApi,
    DomeeApiError,
    DomeeAuthenticationError,
)
from custom_components.domee.button import DomeeButton, async_setup_entry
from custom_components.domee.config_flow import DomeeConfigFlow
from custom_components.domee.const import CONF_BASE_URL, CONF_TOKEN
from custom_components.domee.coordinator import DomeeCoordinator
from custom_components.domee.snapshot import (
    DomeeEntitySnapshot,
    DomeeSnapshot,
    DomeeSnapshotError,
)

INSTANCE_ID = "a0ebcb2a-ef69-4db7-9dca-3dfdcd57364e"


@pytest.mark.parametrize("schema_version", [1, 2])
def test_api_accepts_snapshot_schema_versions(schema_version: int) -> None:
    api = object.__new__(DomeeApi)
    api._request = AsyncMock(
        return_value={
            "schemaVersion": schema_version,
            "account": {"id": "synthetic-account-1"},
            "hubs": [],
            "devices": [],
            "entities": [],
        }
    )

    snapshot = asyncio.run(api.async_get_snapshot())

    assert snapshot.schema_version == schema_version
    api._request.assert_awaited_once_with("GET", "/snapshot")


def test_coordinator_maps_authentication_and_transport_errors() -> None:
    coordinator = object.__new__(DomeeCoordinator)
    coordinator.api = SimpleNamespace(
        async_get_snapshot=AsyncMock(
            side_effect=DomeeAuthenticationError("revoked")
        )
    )
    with pytest.raises(ConfigEntryAuthFailed):
        asyncio.run(coordinator._async_update_data())

    coordinator.api.async_get_snapshot = AsyncMock(
        side_effect=DomeeApiError("offline")
    )
    with pytest.raises(UpdateFailed, match="offline"):
        asyncio.run(coordinator._async_update_data())

    coordinator.api.async_get_snapshot = AsyncMock(
        side_effect=DomeeSnapshotError("schemaVersion is unsupported")
    )
    with pytest.raises(UpdateFailed, match="Invalid Domee snapshot"):
        asyncio.run(coordinator._async_update_data())


def test_integration_setup_unload_and_reload_lifecycle() -> None:
    asyncio.run(_test_integration_setup_unload_and_reload_lifecycle())


async def _test_integration_setup_unload_and_reload_lifecycle() -> None:
    coordinator = Mock()
    coordinator.async_config_entry_first_refresh = AsyncMock()
    config_entries = SimpleNamespace(
        async_forward_entry_setups=AsyncMock(),
        async_unload_platforms=AsyncMock(return_value=True),
    )
    hass = SimpleNamespace(config_entries=config_entries)
    entry = SimpleNamespace(
        data={
            CONF_BASE_URL: "https://domee.example",
            CONF_TOKEN: "dummy-integration-token",
        },
        runtime_data=None,
    )

    with (
        patch(
            "custom_components.domee.async_get_clientsession",
            return_value=Mock(),
        ),
        patch("custom_components.domee.DomeeApi") as api_class,
        patch(
            "custom_components.domee.DomeeCoordinator",
            return_value=coordinator,
        ),
    ):
        assert await async_setup_integration(hass, entry) is True
        assert entry.runtime_data.api is api_class.return_value
        assert entry.runtime_data.coordinator is coordinator
        assert await async_unload_integration(hass, entry) is True
        assert await async_setup_integration(hass, entry) is True

    assert coordinator.async_config_entry_first_refresh.await_count == 2
    assert config_entries.async_forward_entry_setups.await_count == 2
    config_entries.async_unload_platforms.assert_awaited_once()


def test_config_flow_success_and_authentication_failure() -> None:
    asyncio.run(_test_config_flow_success_and_authentication_failure())


async def _test_config_flow_success_and_authentication_failure() -> None:
    assert DomeeConfigFlow.VERSION == 1
    flow = object.__new__(DomeeConfigFlow)
    flow.hass = Mock()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = Mock()
    flow.async_create_entry = Mock(return_value={"type": "create_entry"})
    flow.async_show_form = Mock(return_value={"type": "form"})

    api = Mock()
    api.async_get_snapshot = AsyncMock(
        return_value=SimpleNamespace(
            account_id="synthetic-account-1",
            backend_instance_id=INSTANCE_ID,
        )
    )
    with (
        patch(
            "custom_components.domee.config_flow.async_get_clientsession",
            return_value=Mock(),
        ),
        patch(
            "custom_components.domee.config_flow.DomeeApi",
            return_value=api,
        ),
    ):
        result = await flow.async_step_user(
            {CONF_BASE_URL: "http://server/", CONF_TOKEN: "dummy-integration-token"}
        )

    assert result == {"type": "create_entry"}
    flow.async_set_unique_id.assert_awaited_once_with(
        f"domee:{INSTANCE_ID}:synthetic-account-1"
    )
    flow._abort_if_unique_id_configured.assert_called_once_with()
    flow.async_create_entry.assert_called_once_with(
        title="Domee",
        data={CONF_BASE_URL: "http://server", CONF_TOKEN: "dummy-integration-token"},
    )

    api.async_get_snapshot = AsyncMock(
        side_effect=DomeeAuthenticationError("invalid")
    )
    with (
        patch(
            "custom_components.domee.config_flow.async_get_clientsession",
            return_value=Mock(),
        ),
        patch(
            "custom_components.domee.config_flow.DomeeApi",
            return_value=api,
        ),
    ):
        result = await flow.async_step_user(
            {CONF_BASE_URL: "http://server", CONF_TOKEN: "dummy-invalid-token"}
        )

    assert result == {"type": "form"}
    assert flow.async_show_form.call_args.kwargs["errors"] == {
        "base": "invalid_auth"
    }

    api.async_get_snapshot = AsyncMock(
        side_effect=DomeeSnapshotError("unsupported schema")
    )
    with (
        patch(
            "custom_components.domee.config_flow.async_get_clientsession",
            return_value=Mock(),
        ),
        patch(
            "custom_components.domee.config_flow.DomeeApi",
            return_value=api,
        ),
    ):
        result = await flow.async_step_user(
            {CONF_BASE_URL: "http://server", CONF_TOKEN: "dummy-integration-token"}
        )

    assert result == {"type": "form"}
    assert flow.async_show_form.call_args.kwargs["errors"] == {
        "base": "invalid_response"
    }


def test_config_flow_rejects_missing_backend_instance_id() -> None:
    asyncio.run(_test_config_flow_rejects_missing_backend_instance_id())


def test_config_flow_identity_is_stable_across_base_urls() -> None:
    asyncio.run(_test_config_flow_identity_is_stable_across_base_urls())


async def _test_config_flow_identity_is_stable_across_base_urls() -> None:
    assigned_ids = []
    api = Mock()
    api.async_get_snapshot = AsyncMock(
        return_value=SimpleNamespace(
            account_id="synthetic-account-1",
            backend_instance_id=INSTANCE_ID,
        )
    )

    for base_url in ("https://domee.example", "https://alias.example/"):
        flow = object.__new__(DomeeConfigFlow)
        flow.hass = Mock()
        flow.async_set_unique_id = AsyncMock(
            side_effect=lambda unique_id: assigned_ids.append(unique_id)
        )
        flow._abort_if_unique_id_configured = Mock()
        flow.async_create_entry = Mock(return_value={"type": "create_entry"})

        with (
            patch(
                "custom_components.domee.config_flow.async_get_clientsession",
                return_value=Mock(),
            ),
            patch(
                "custom_components.domee.config_flow.DomeeApi",
                return_value=api,
            ),
        ):
            result = await flow.async_step_user(
                {CONF_BASE_URL: base_url, CONF_TOKEN: "dummy-integration-token"}
            )

        assert result == {"type": "create_entry"}
        flow._abort_if_unique_id_configured.assert_called_once_with()

    assert assigned_ids == [
        f"domee:{INSTANCE_ID}:synthetic-account-1",
        f"domee:{INSTANCE_ID}:synthetic-account-1",
    ]


async def _test_config_flow_rejects_missing_backend_instance_id() -> None:
    flow = object.__new__(DomeeConfigFlow)
    flow.hass = Mock()
    flow.async_set_unique_id = AsyncMock()
    flow._abort_if_unique_id_configured = Mock()
    flow.async_create_entry = Mock()
    flow.async_show_form = Mock(return_value={"type": "form"})
    api = Mock()
    api.async_get_snapshot = AsyncMock(
        return_value=SimpleNamespace(
            account_id="synthetic-account-1",
            backend_instance_id=None,
        )
    )

    with (
        patch(
            "custom_components.domee.config_flow.async_get_clientsession",
            return_value=Mock(),
        ),
        patch(
            "custom_components.domee.config_flow.DomeeApi",
            return_value=api,
        ),
    ):
        result = await flow.async_step_user(
            {CONF_BASE_URL: "http://server", CONF_TOKEN: "dummy-integration-token"}
        )

    assert result == {"type": "form"}
    assert flow.async_show_form.call_args.kwargs["errors"] == {
        "base": "missing_instance_id"
    }
    flow.async_set_unique_id.assert_not_awaited()
    flow.async_create_entry.assert_not_called()


def test_reauth_requires_same_stable_identity() -> None:
    asyncio.run(_test_reauth_requires_same_stable_identity())


async def _test_reauth_requires_same_stable_identity() -> None:
    entry = SimpleNamespace(
        data={CONF_BASE_URL: "http://server", CONF_TOKEN: "dummy-old-token"},
        unique_id=f"domee:{INSTANCE_ID}:synthetic-account-1",
    )
    flow = object.__new__(DomeeConfigFlow)
    flow._reauth_entry = entry
    flow.hass = Mock()
    flow.async_update_reload_and_abort = Mock(
        return_value={"type": "abort"}
    )
    flow.async_show_form = Mock(return_value={"type": "form"})
    api = Mock()

    with (
        patch(
            "custom_components.domee.config_flow.async_get_clientsession",
            return_value=Mock(),
        ),
        patch(
            "custom_components.domee.config_flow.DomeeApi",
            return_value=api,
        ),
    ):
        api.async_get_snapshot = AsyncMock(
            return_value=SimpleNamespace(
                account_id="synthetic-account-1",
                backend_instance_id=INSTANCE_ID,
            )
        )
        result = await flow.async_step_reauth_confirm(
            {CONF_TOKEN: "dummy-new-token"}
        )
        assert result == {"type": "abort"}
        flow.async_update_reload_and_abort.assert_called_once_with(
            entry,
            data={
                CONF_BASE_URL: "http://server",
                CONF_TOKEN: "dummy-new-token",
            },
        )

        api.async_get_snapshot = AsyncMock(
            return_value=SimpleNamespace(
                account_id="other-account",
                backend_instance_id=INSTANCE_ID,
            )
        )
        result = await flow.async_step_reauth_confirm(
            {CONF_TOKEN: "dummy-wrong-account-token"}
        )
        assert result == {"type": "form"}
        assert flow.async_show_form.call_args.kwargs["errors"] == {
            "base": "wrong_identity"
        }

        api.async_get_snapshot = AsyncMock(
            return_value=SimpleNamespace(
                account_id="synthetic-account-1",
                backend_instance_id="588b8e81-fbd8-4bd4-8425-201b85ea7155",
            )
        )
        result = await flow.async_step_reauth_confirm(
            {CONF_TOKEN: "dummy-wrong-backend-token"}
        )

    assert result == {"type": "form"}
    assert flow.async_show_form.call_args.kwargs["errors"] == {
        "base": "wrong_identity"
    }
    assert flow.async_update_reload_and_abort.call_count == 1


def test_phase1_button_setup_deduplicates_and_press_still_refreshes() -> None:
    asyncio.run(_test_phase1_button_setup_deduplicates_and_press_still_refreshes())


async def _test_phase1_button_setup_deduplicates_and_press_still_refreshes() -> None:
    description = DomeeEntitySnapshot(
        unique_id="domee_button_button-1",
        platform="button",
        action_type="button",
        source_id="button-1",
        hub_id="synthetic-hub-1",
        device_identifier="domee_hub_synthetic-hub-1",
        name="Power",
        available=True,
        can_control=True,
    )
    listeners = []
    coordinator = SimpleNamespace(
        data=DomeeSnapshot(2, "synthetic-account-1", (), (), (description,)),
        async_add_listener=lambda listener: listeners.append(listener) or Mock(),
    )
    entry = SimpleNamespace(
        runtime_data=SimpleNamespace(coordinator=coordinator, api=Mock()),
        async_on_unload=Mock(),
    )
    add_entities = Mock()

    with patch(
        "custom_components.domee.button.DomeeButton",
        side_effect=lambda runtime, item: item.unique_id,
    ):
        await async_setup_entry(Mock(), entry, add_entities)
        listeners[0]()

    add_entities.assert_called_once_with(["domee_button_button-1"])

    button = object.__new__(DomeeButton)
    button.description = description
    button.refresh_description = Mock()
    button._api = SimpleNamespace(async_press_button=AsyncMock())
    button.coordinator = SimpleNamespace(async_request_refresh=AsyncMock())
    await button.async_press()

    button._api.async_press_button.assert_awaited_once_with(
        "synthetic-hub-1", "button-1"
    )
    button.coordinator.async_request_refresh.assert_awaited_once()
