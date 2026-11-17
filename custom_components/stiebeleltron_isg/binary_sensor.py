"""Binary indicators exposed by the ISG."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import StiebelEltronIsgConfigEntry
from .scraper import KIND_BINARY
from .sensor import StiebelEltronIsgMetricEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StiebelEltronIsgConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Discover binary indicators on initial and subsequent refreshes."""
    coordinator = entry.runtime_data.coordinator
    known_keys: set[str] = set()

    def add_new_sensors() -> None:
        keys = {
            key for key, metric in coordinator.data.metrics.items() if metric.kind == KIND_BINARY
        } - known_keys
        if keys:
            known_keys.update(keys)
            async_add_entities(StiebelEltronIsgBinarySensor(entry, key) for key in sorted(keys))

    add_new_sensors()
    entry.async_on_unload(coordinator.async_add_listener(add_new_sensors))


class StiebelEltronIsgBinarySensor(StiebelEltronIsgMetricEntity, BinarySensorEntity):
    """An ISG on/off indicator."""

    @property
    def is_on(self) -> bool | None:
        """Return a boolean, or unknown for an unrecognized indicator value."""
        value = self.metric.value
        return value if isinstance(value, bool) else None
