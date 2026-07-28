"""Stateful Wi-Fi switch entities."""

from __future__ import annotations

import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DomeeRuntimeData
from .entity import DomeeEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry[DomeeRuntimeData],
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Add and discover Domee Wi-Fi switch entities."""
    runtime = entry.runtime_data
    known: set[str] = set()

    def add_new_entities() -> None:
        entities = []
        for description in runtime.coordinator.data.entities:
            if description.platform != "switch":
                continue
            unique_id = description.unique_id
            if unique_id in known:
                continue
            known.add(unique_id)
            entities.append(DomeeSwitch(runtime, description))
        if entities:
            async_add_entities(entities)

    add_new_entities()
    entry.async_on_unload(runtime.coordinator.async_add_listener(add_new_entities))


class DomeeSwitch(DomeeEntity, SwitchEntity):
    """One authoritative Wi-Fi switch channel."""

    def __init__(self, runtime: DomeeRuntimeData, description) -> None:
        super().__init__(runtime.coordinator, description)
        self._api = runtime.api

    @property
    def is_on(self) -> bool | None:
        """Return the last power state reported by the physical switch."""
        self.refresh_description()
        power = self.description.power
        return power if isinstance(power, bool) else None

    @property
    def available(self) -> bool:
        """Return whether the physical switch is reachable and controllable."""
        self.refresh_description()
        still_present = any(
            entity.unique_id == self._attr_unique_id
            for entity in self.coordinator.data.entities
        )
        return (
            self.coordinator.last_update_success
            and still_present
            and self.description.available
            and self.description.can_control
        )

    async def _async_set_power(self, value: bool) -> None:
        self.refresh_description()
        await self._api.async_set_switch_power(
            self.description.device_id,
            self.description.channel,
            value,
        )
        # Give the MQTT report a short bounded window to reach the backend cache.
        await asyncio.sleep(0.5)
        await self.coordinator.async_request_refresh()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the physical switch channel."""
        await self._async_set_power(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the physical switch channel."""
        await self._async_set_power(False)
