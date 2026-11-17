"""ISG on/off settings."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import StiebelEltronIsgConfigEntry
from .control_entity import IsgControlEntity
from .controls import CONTROLS


async def async_setup_entry(
    hass: HomeAssistant, entry: StiebelEltronIsgConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add verified switches and discover any that become available later."""
    coordinator = entry.runtime_data.controls
    known: set[str] = set()

    def discover() -> None:
        new = [
            c
            for c in CONTROLS
            if c.mode == "switch" and c.key in coordinator.data and c.key not in known
        ]
        if new:
            known.update(c.key for c in new)
            async_add_entities(IsgSwitch(entry, c) for c in new)

    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))


class IsgSwitch(IsgControlEntity, SwitchEntity):
    """An individual on/off setting."""

    @property
    def is_on(self) -> bool | None:
        value = self.coordinator.data.get(self.control.key)
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.async_write_control(True)

    async def async_turn_off(self, **kwargs) -> None:
        await self.async_write_control(False)
