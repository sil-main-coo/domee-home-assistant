"""HTTP client for the Domee server."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aiohttp import ClientError, ClientResponseError, ClientSession

from .snapshot import DomeeSnapshot, parse_snapshot


class DomeeApiError(Exception):
    """Base Domee API error."""


class DomeeAuthenticationError(DomeeApiError):
    """Domee rejected the integration token."""


class DomeeApi:
    """Small async client for the Home Assistant endpoints."""

    def __init__(self, session: ClientSession, base_url: str, token: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
        timeout: int = 15,
    ) -> Any:
        try:
            async with self._session.request(
                method,
                f"{self._base_url}/api/v1/home-assistant{path}",
                headers=self._headers,
                json=json,
                timeout=timeout,
            ) as response:
                if response.status == 401:
                    raise DomeeAuthenticationError("Invalid Domee token")
                response.raise_for_status()
                payload = await response.json()
        except DomeeAuthenticationError:
            raise
        except (ClientError, ClientResponseError, TimeoutError, ValueError) as error:
            raise DomeeApiError(str(error)) from error

        if not isinstance(payload, dict) or "data" not in payload:
            raise DomeeApiError("Unexpected Domee response")
        return payload["data"]

    async def async_get_snapshot(self) -> DomeeSnapshot:
        """Fetch all HA-visible hubs and entities in one request."""
        return parse_snapshot(await self._request("GET", "/snapshot"))

    async def async_press_button(self, hub_id: str, button_id: str) -> None:
        """Send one remote button command."""
        await self._request(
            "POST",
            "/commands",
            {"hubId": hub_id, "buttonId": button_id},
        )

    async def async_execute_script(self, script_id: str) -> None:
        """Execute one Domee script."""
        await self._request(
            "POST",
            f"/scripts/{script_id}/execute",
            timeout=120,
        )

    async def async_set_switch_power(
        self, device_id: str, channel: int, value: bool
    ) -> None:
        """Set one Wi-Fi switch channel through the domain command API."""
        await self._request(
            "POST",
            f"/devices/{device_id}/commands",
            {
                "capability": "power",
                "channel": channel,
                "value": value,
                "requestId": str(uuid4()),
            },
        )
