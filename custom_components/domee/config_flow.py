"""Config flow for Domee."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DomeeApi, DomeeApiError, DomeeAuthenticationError
from .const import CONF_BASE_URL, CONF_TOKEN, DOMAIN
from .identity import (
    DomeeIdentityError,
    DomeeMissingInstanceIdError,
    build_config_entry_unique_id,
)
from .snapshot import DomeeSnapshotError


class DomeeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure a Domee server and integration token."""

    VERSION = 1
    _reauth_entry: config_entries.ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}
        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            api = DomeeApi(
                async_get_clientsession(self.hass),
                base_url,
                user_input[CONF_TOKEN],
            )
            try:
                snapshot = await api.async_get_snapshot()
            except DomeeAuthenticationError:
                errors["base"] = "invalid_auth"
            except DomeeApiError:
                errors["base"] = "cannot_connect"
            except DomeeSnapshotError:
                errors["base"] = "invalid_response"
            else:
                try:
                    unique_id = build_config_entry_unique_id(
                        snapshot.backend_instance_id,
                        snapshot.account_id,
                    )
                except DomeeMissingInstanceIdError:
                    errors["base"] = "missing_instance_id"
                except DomeeIdentityError:
                    errors["base"] = "invalid_response"
                else:
                    await self.async_set_unique_id(unique_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title="Domee",
                        data={
                            CONF_BASE_URL: base_url,
                            CONF_TOKEN: user_input[CONF_TOKEN],
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL): str,
                vol.Required(CONF_TOKEN): str,
            }
        )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> FlowResult:
        """Start token replacement after authentication failure."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate and store a replacement integration token."""
        errors: dict[str, str] = {}
        if self._reauth_entry is None:
            return self.async_abort(reason="reauth_entry_missing")

        if user_input is not None:
            api = DomeeApi(
                async_get_clientsession(self.hass),
                self._reauth_entry.data[CONF_BASE_URL],
                user_input[CONF_TOKEN],
            )
            try:
                snapshot = await api.async_get_snapshot()
            except DomeeAuthenticationError:
                errors["base"] = "invalid_auth"
            except DomeeApiError:
                errors["base"] = "cannot_connect"
            except DomeeSnapshotError:
                errors["base"] = "invalid_response"
            else:
                try:
                    expected_unique_id = build_config_entry_unique_id(
                        snapshot.backend_instance_id,
                        snapshot.account_id,
                    )
                except DomeeMissingInstanceIdError:
                    errors["base"] = "missing_instance_id"
                except DomeeIdentityError:
                    errors["base"] = "invalid_response"
                if (
                    not errors
                    and expected_unique_id != self._reauth_entry.unique_id
                ):
                    errors["base"] = "wrong_identity"
                elif not errors:
                    return self.async_update_reload_and_abort(
                        self._reauth_entry,
                        data={
                            **self._reauth_entry.data,
                            CONF_TOKEN: user_input[CONF_TOKEN],
                        },
                    )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_TOKEN): str}),
            errors=errors,
        )
