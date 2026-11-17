"""ISG option settings."""

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import StiebelEltronIsgConfigEntry
from .control_entity import IsgControlEntity
from .controls import CONTROLS


async def async_setup_entry(
    hass: HomeAssistant, entry: StiebelEltronIsgConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data.controls
    known: set[str] = set()

    def discover() -> None:
        new = [
            c
            for c in CONTROLS
            if c.mode == "select" and c.key in coordinator.data and c.key not in known
        ]
        if new:
            known.update(c.key for c in new)
            async_add_entities(IsgSelect(entry, c) for c in new)

    discover()
    entry.async_on_unload(coordinator.async_add_listener(discover))


class IsgSelect(IsgControlEntity, SelectEntity):
    """A verified selection from the device form."""

    _attr_options = ["GEBLÄSEKÜHLUNG", "FLÄCHENKÜHLUNG"]

    @property
    def current_option(self) -> str | None:
        value = self.coordinator.data.get(self.control.key)
        return value if isinstance(value, str) else None

    async def async_select_option(self, option: str) -> None:
        await self.async_write_control(option)
