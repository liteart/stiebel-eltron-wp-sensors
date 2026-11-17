"""Shared entity behavior for writable ISG settings."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import StiebelEltronIsgConfigEntry
from .const import DOMAIN, NAME
from .controls import Control


class IsgControlEntity(CoordinatorEntity):
    """A setting tied to the validated control coordinator."""

    _attr_has_entity_name = True

    def __init__(self, entry: StiebelEltronIsgConfigEntry, control: Control) -> None:
        super().__init__(entry.runtime_data.controls)
        self._entry = entry
        self.control = control
        self._attr_unique_id = f"{entry.entry_id}_control_{control.key}"
        self._attr_name = control.name

    @property
    def available(self) -> bool:
        return super().available and self.control.key in self.coordinator.data

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title or NAME,
            manufacturer="Stiebel Eltron",
            model="ISG",
        )

    async def async_write_control(self, value: float | bool | str) -> None:
        try:
            await self.coordinator.controls.async_write(self.control, value)
        finally:
            await self.coordinator.async_request_refresh()
