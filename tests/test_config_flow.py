"""Tests for the ISG config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from custom_components.stiebeleltron_isg.client import (
    StiebelEltronIsgAuthRequiredError,
    StiebelEltronIsgInvalidAuthError,
)
from custom_components.stiebeleltron_isg.const import CONF_SCAN_INTERVAL, CONF_TIMEOUT, DOMAIN


@pytest.mark.asyncio
async def test_config_flow_creates_entry_without_credentials(
    hass,
    no_auth_host: str,
) -> None:
    """The flow should create an entry if the page is publicly accessible."""
    with patch(
        "homeassistant.config_entries.ConfigEntries.async_setup",
        new=AsyncMock(return_value=True),
    ), patch(
        "custom_components.stiebeleltron_isg.config_flow._async_validate_input",
        new=AsyncMock(return_value=no_auth_host),
    ), patch(
        "custom_components.stiebeleltron_isg.async_setup_entry",
        new=AsyncMock(return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: no_auth_host,
                CONF_SCAN_INTERVAL: 5,
                CONF_TIMEOUT: 10,
            },
        )

    assert result["type"] == "create_entry"
    assert result["data"][CONF_HOST] == no_auth_host
    await hass.async_stop(force=True)


@pytest.mark.asyncio
async def test_config_flow_requires_credentials_for_login_page(
    hass,
    auth_host: str,
) -> None:
    """The flow should block setup until credentials are provided."""
    with patch(
        "custom_components.stiebeleltron_isg.config_flow._async_validate_input",
        new=AsyncMock(side_effect=StiebelEltronIsgAuthRequiredError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: auth_host,
                CONF_SCAN_INTERVAL: 5,
                CONF_TIMEOUT: 10,
            },
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "credentials_required"}
    await hass.async_stop(force=True)


@pytest.mark.asyncio
async def test_config_flow_rejects_invalid_credentials(
    hass,
    auth_host: str,
) -> None:
    """The flow should reject wrong credentials."""
    with patch(
        "custom_components.stiebeleltron_isg.config_flow._async_validate_input",
        new=AsyncMock(side_effect=StiebelEltronIsgInvalidAuthError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: auth_host,
                CONF_USERNAME: "demo_user",
                CONF_PASSWORD: "wrong",
                CONF_SCAN_INTERVAL: 5,
                CONF_TIMEOUT: 10,
            },
        )

    assert result["type"] == "form"
    assert result["errors"] == {"base": "invalid_auth"}
    await hass.async_stop(force=True)
