"""Tests for ISG diagnostics."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stiebeleltron_isg.const import CONF_SCAN_INTERVAL, CONF_TIMEOUT, DOMAIN
from custom_components.stiebeleltron_isg.diagnostics import async_get_config_entry_diagnostics
from custom_components.stiebeleltron_isg.scraper import (
    merge_snapshots,
    parse_heat_pump_page,
    parse_plant_page,
)


@pytest.mark.asyncio
async def test_diagnostics_redacts_sensitive_values(
    hass,
    heat_pump_page: str,
    anlage_page: str,
    no_auth_host: str,
) -> None:
    """Diagnostics should redact configured connection details."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=f"ISG ({no_auth_host})",
        data={
            CONF_HOST: no_auth_host,
            CONF_USERNAME: "demo_user",
            CONF_PASSWORD: "demo_password",
        },
        options={CONF_SCAN_INTERVAL: 5, CONF_TIMEOUT: 10},
    )
    entry.runtime_data = SimpleNamespace(
        coordinator=SimpleNamespace(
            data=merge_snapshots(
                parse_heat_pump_page(heat_pump_page),
                parse_plant_page(anlage_page),
            )
        )
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert no_auth_host not in str(diagnostics)
    assert diagnostics["entry"]["data"][CONF_HOST] == "**REDACTED**"
    assert diagnostics["entry"]["data"][CONF_USERNAME] == "**REDACTED**"
    assert diagnostics["entry"]["data"][CONF_PASSWORD] == "**REDACTED**"
    assert diagnostics["snapshot"]["metric_count"] == 67
