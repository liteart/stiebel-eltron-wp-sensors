"""Diagnostics support for the Stiebel Eltron ISG integration."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from . import StiebelEltronIsgConfigEntry

TO_REDACT = {CONF_HOST, CONF_USERNAME, CONF_PASSWORD}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: StiebelEltronIsgConfigEntry,
) -> dict:
    """Return diagnostics for a config entry."""
    snapshot = entry.runtime_data.coordinator.data
    return {
        "entry": async_redact_data(
            {
                "data": dict(entry.data),
                "options": dict(entry.options),
            },
            TO_REDACT,
        ),
        "snapshot": {
            "metric_count": len(snapshot.metrics),
            "metric_keys": sorted(snapshot.metrics),
            "software_version": snapshot.software_version,
            "sections": snapshot.sections,
        },
    }
