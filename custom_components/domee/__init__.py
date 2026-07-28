"""Domee Home Assistant integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DomeeApi
from .const import CONF_BASE_URL, CONF_TOKEN, PLATFORMS
from .coordinator import DomeeCoordinator


@dataclass
class DomeeRuntimeData:
    """Runtime objects owned by one config entry."""

    api: DomeeApi
    coordinator: DomeeCoordinator


type DomeeConfigEntry = ConfigEntry[DomeeRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant, entry: DomeeConfigEntry
) -> bool:
    """Set up Domee from a config entry."""
    api = DomeeApi(
        async_get_clientsession(hass),
        entry.data[CONF_BASE_URL],
        entry.data[CONF_TOKEN],
    )
    coordinator = DomeeCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = DomeeRuntimeData(api=api, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: DomeeConfigEntry
) -> bool:
    """Unload one Domee config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
