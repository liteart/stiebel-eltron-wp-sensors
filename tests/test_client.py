"""Tests for the ISG HTTP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import ClientSession

from custom_components.stiebeleltron_isg.client import (
    StiebelEltronIsgAuthRequiredError,
    StiebelEltronIsgCannotConnectError,
    StiebelEltronIsgClient,
    StiebelEltronIsgInvalidAuthError,
)


@pytest.mark.asyncio
async def test_client_fetches_snapshot_without_auth(
    heat_pump_page: str,
    anlage_page: str,
) -> None:
    """The client should parse the heat pump page directly when no auth is required."""
    client = StiebelEltronIsgClient(
        session=MagicMock(spec=ClientSession),
        host="isg-no-auth.local",
        timeout=5,
    )
    client._async_request = AsyncMock(  # type: ignore[method-assign]
        side_effect=[heat_pump_page, anlage_page, "", "", "", ""]
    )

    snapshot = await client.async_get_snapshot()

    assert len(snapshot.metrics) == 65
    assert snapshot.software_version == "v12.2.3"
    assert snapshot.metrics["heizung__aussentemperatur"].value == 8.9


@pytest.mark.asyncio
async def test_client_fetches_snapshot_with_auth(
    login_page: str,
    heat_pump_page: str,
    anlage_page: str,
) -> None:
    """The client should log in when the ISG requires authentication."""
    client = StiebelEltronIsgClient(
        session=MagicMock(spec=ClientSession),
        host="isg-auth.local",
        username="demo_user",
        password="demo_password",
        timeout=5,
    )
    client._async_request = AsyncMock(  # type: ignore[method-assign]
        side_effect=[login_page, heat_pump_page, login_page, anlage_page, "", "", "", ""]
    )

    snapshot = await client.async_get_snapshot()

    assert snapshot.logged_in_user == "demo_user"
    assert snapshot.metrics["starts__verdichter"].value == 3287
    assert snapshot.metrics["energiemanagement__deaktiviert"].value is True


@pytest.mark.asyncio
async def test_client_requires_credentials_for_login_page(login_page: str) -> None:
    """The client should surface auth-required when the login page is returned."""
    client = StiebelEltronIsgClient(
        session=MagicMock(spec=ClientSession),
        host="isg-auth.local",
        timeout=5,
    )
    client._async_request = AsyncMock(return_value=login_page)  # type: ignore[method-assign]

    with pytest.raises(StiebelEltronIsgAuthRequiredError):
        await client.async_get_snapshot()


@pytest.mark.asyncio
async def test_client_rejects_invalid_credentials(
    login_page: str,
    login_failed_page: str,
) -> None:
    """The client should reject invalid credentials."""
    client = StiebelEltronIsgClient(
        session=MagicMock(spec=ClientSession),
        host="isg-auth.local",
        username="demo_user",
        password="wrong",
        timeout=5,
    )
    client._async_request = AsyncMock(  # type: ignore[method-assign]
        side_effect=[login_page, login_failed_page]
    )

    with pytest.raises(StiebelEltronIsgInvalidAuthError):
        await client.async_get_snapshot()


async def test_timeout_is_reported_as_connection_failure() -> None:
    """Timeouts are translated into the integration's connection error."""
    session = MagicMock(spec=ClientSession)
    session.request.side_effect = TimeoutError()
    client = StiebelEltronIsgClient(session=session, host="isg.local")
    with pytest.raises(StiebelEltronIsgCannotConnectError):
        await client.async_probe()


async def test_optional_pages_are_isolated(heat_pump_page: str, anlage_page: str) -> None:
    """Read additional metrics even when another optional page is unsupported."""
    extra_page = """<div id="sub_nav"><span class="main">STATUS ANLAGE</span></div>
    <table class="info"><tr><th>BETRIEBSSTATUS</th></tr>
    <tr><td class="key">PUMPE</td><td class="value">An</td></tr></table>"""
    client = StiebelEltronIsgClient(session=MagicMock(spec=ClientSession), host="isg.local")
    client._async_request = AsyncMock(  # type: ignore[method-assign]
        side_effect=[heat_pump_page, anlage_page, "", extra_page, "", ""]
    )
    snapshot = await client.async_get_snapshot()
    assert snapshot.metrics["status_anlage_betriebsstatus__pumpe"].value is True
    assert "starts__verdichter" in snapshot.metrics
