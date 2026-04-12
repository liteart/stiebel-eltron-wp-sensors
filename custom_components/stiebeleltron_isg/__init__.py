"""The Stiebel Eltron ISG integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import StiebelEltronIsgClient
from .const import CONF_TIMEOUT, DEFAULT_TIMEOUT, DOMAIN, PLATFORMS
from .coordinator import StiebelEltronIsgDataUpdateCoordinator


@dataclass(slots=True)
class StiebelEltronIsgRuntimeData:
    """Runtime data for a config entry."""

    client: StiebelEltronIsgClient
    coordinator: StiebelEltronIsgDataUpdateCoordinator


type StiebelEltronIsgConfigEntry = ConfigEntry[StiebelEltronIsgRuntimeData]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: StiebelEltronIsgConfigEntry) -> bool:
    """Set up Stiebel Eltron ISG from a config entry."""
    client = StiebelEltronIsgClient(
        session=async_get_clientsession(hass),
        host=entry.data["host"],
        username=entry.data.get("username", ""),
        password=entry.data.get("password", ""),
        timeout=float(entry.options.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)),
    )
    coordinator = StiebelEltronIsgDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = StiebelEltronIsgRuntimeData(client=client, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: StiebelEltronIsgConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(hass: HomeAssistant, entry: StiebelEltronIsgConfigEntry) -> None:
    """Reload the config entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)
