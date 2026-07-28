"""Snapshot coordinator for Domee."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DomeeApi, DomeeApiError, DomeeAuthenticationError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .snapshot import DomeeSnapshot, DomeeSnapshotError

_LOGGER = logging.getLogger(__name__)


class DomeeCoordinator(DataUpdateCoordinator[DomeeSnapshot]):
    """Poll one consolidated snapshot for all Domee entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: DomeeApi,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=DEFAULT_SCAN_INTERVAL,
            always_update=False,
        )
        self.api = api

    async def _async_update_data(self) -> DomeeSnapshot:
        try:
            return await self.api.async_get_snapshot()
        except DomeeAuthenticationError as error:
            raise ConfigEntryAuthFailed from error
        except DomeeApiError as error:
            raise UpdateFailed(str(error)) from error
        except DomeeSnapshotError as error:
            raise UpdateFailed(f"Invalid Domee snapshot: {error}") from error
