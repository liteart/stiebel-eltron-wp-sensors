"""Coordinator for Stiebel Eltron ISG data updates."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import (
    StiebelEltronIsgAuthRequiredError,
    StiebelEltronIsgCannotConnectError,
    StiebelEltronIsgClient,
    StiebelEltronIsgInvalidAuthError,
    StiebelEltronIsgParseError,
)
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN
from .controls import IsgControls
from .scraper import IntegrationSnapshot

LOGGER = logging.getLogger(__name__)


class StiebelEltronIsgControlsCoordinator(DataUpdateCoordinator[dict[str, float | bool | str]]):
    """Poll validated settings separately from the read-only measurements."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, controls: IsgControls) -> None:
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_controls",
            update_interval=timedelta(
                minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
            ),
        )
        self.controls = controls

    async def _async_update_data(self) -> dict[str, float | bool | str]:
        return await self.controls.async_read()


class StiebelEltronIsgDataUpdateCoordinator(DataUpdateCoordinator[IntegrationSnapshot]):
    """Manage fetching ISG data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: StiebelEltronIsgClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(
                minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES)
            ),
        )
        self.client = client
        self.config_entry = entry

    async def _async_update_data(self) -> IntegrationSnapshot:
        """Fetch data from the ISG."""
        try:
            return await self.client.async_get_snapshot()
        except StiebelEltronIsgInvalidAuthError as err:
            raise ConfigEntryAuthFailed from err
        except StiebelEltronIsgAuthRequiredError as err:
            raise ConfigEntryAuthFailed from err
        except StiebelEltronIsgCannotConnectError as err:
            raise UpdateFailed(f"Cannot connect to ISG: {err}") from err
        except StiebelEltronIsgParseError as err:
            raise UpdateFailed(f"Could not parse ISG page: {err}") from err
