"""ISG numeric settings."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import StiebelEltronIsgConfigEntry
from .control_entity import IsgControlEntity
from .controls import CONTROLS, Control


async def async_setup_entry(
    hass: HomeAssistant, entry: StiebelEltronIsgConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add only settings recognized on this device, including later discoveries."""
    coordinator = entry.runtime_data.controls
    known: set[str] = set()

    def discover() -> None:
        new = [
            c
            for c in CONTROLS
            if c.mode == "number" and c.key in coordinator.data and c.key not in known
        ]
        if new:
            known.update(c.key for c in new)
            async_add_entities(IsgNumber(entry, c) for c in new)

    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))


class IsgNumber(IsgControlEntity, NumberEntity):
    """An individual numeric setting."""

    _attr_mode = NumberMode.BOX

    def __init__(self, entry: StiebelEltronIsgConfigEntry, control: Control) -> None:
        super().__init__(entry, control)
        self._attr_native_min_value = control.minimum
        self._attr_native_max_value = control.maximum
        self._attr_native_step = control.step
        self._attr_native_unit_of_measurement = control.unit

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.get(self.control.key)
        return float(value) if value is not None and not isinstance(value, bool) else None

    async def async_set_native_value(self, value: float) -> None:
        await self.async_write_control(value)
