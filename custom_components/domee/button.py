"""Button entities for remote commands and scripts."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
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
    """Add and discover Domee button entities."""
    runtime = entry.runtime_data
    known: set[str] = set()

    def add_new_entities() -> None:
        entities = []
        for description in runtime.coordinator.data.entities:
            if description.platform != "button":
                continue
            unique_id = description.unique_id
            if unique_id in known:
                continue
            known.add(unique_id)
            entities.append(DomeeButton(runtime, description))
        if entities:
            async_add_entities(entities)

    add_new_entities()
    entry.async_on_unload(runtime.coordinator.async_add_listener(add_new_entities))


class DomeeButton(DomeeEntity, ButtonEntity):
    """One stateless Domee remote command or script."""

    def __init__(self, runtime: DomeeRuntimeData, description) -> None:
        super().__init__(runtime.coordinator, description)
        self._api = runtime.api

    async def async_press(self) -> None:
        """Execute the represented Domee action."""
        self.refresh_description()
        if self.description.action_type == "script":
            await self._api.async_execute_script(self.description.source_id)
        else:
            await self._api.async_press_button(
                self.description.hub_id,
                self.description.source_id,
            )
        await self.coordinator.async_request_refresh()
