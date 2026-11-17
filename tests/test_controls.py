"""Tests for validated ISG control writes; no real device is changed."""

from __future__ import annotations

import json
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.exceptions import HomeAssistantError

from custom_components.stiebeleltron_isg.client import StiebelEltronIsgAuthRequiredError
from custom_components.stiebeleltron_isg.controls import (
    CONTROLS,
    HOLIDAY,
    Control,
    IsgControls,
    parse_control,
)


def number_page(control: Control, value: str = "22,0") -> str:
    """Build a minimal representative settings form."""
    tab = f"$(\"#subnavactivename\").html('{control.tab}');" if control.tab else ""
    return f"""
    <div id="sub_nav"><div class="main">{control.title}</div></div>
    <script>{tab}</script><form id="werte"><div id="calval{control.field}">
    <h3 class="title">{control.label}</h3><input name="val{control.field}" type="text">
    <a onmousedown="change('val{control.field}','+',
       {control.minimum},{control.maximum},'{control.step}',true)"></a>
    <script>valSettings['val{control.field}']['min'] = '{control.minimum}';
    valSettings['val{control.field}']['max'] = '{control.maximum}';
    jsvalues['{control.field}']['val']='{value}';</script></div></form>"""


def test_control_checks_page_field_and_limits() -> None:
    control = next(c for c in CONTROLS if c.key == "heating_2_comfort")
    page = number_page(control)
    assert parse_control(page, control) == 22.0
    assert parse_control(page.replace("HEIZKREIS 2", "HEIZKREIS 1"), control) is None
    assert parse_control(page.replace("KOMFORT TEMPERATUR", "ECO TEMPERATUR"), control) is None
    assert parse_control(page.replace("'0.1'", "'0.5'"), control) is None


async def test_number_write_validates_sends_and_reads_back() -> None:
    control = next(c for c in CONTROLS if c.key == "heating_2_comfort")
    client = MagicMock(host="isg.local")
    client._async_request = AsyncMock(return_value='{"success": true}')
    controls = IsgControls(client)
    controls._page = AsyncMock(side_effect=[number_page(control), number_page(control, "22,5")])
    await controls.async_write(control, 22.5)
    call = client._async_request.call_args
    assert call.args == ("POST", "http://isg.local/save.php")
    assert json.loads(call.kwargs["data"]["data"]) == [{"name": "val10980", "value": "22,5"}]


async def test_rejects_bad_values_and_unverified_write() -> None:
    control = next(c for c in CONTROLS if c.key == "heating_2_comfort")
    client = MagicMock(host="isg.local")
    client._async_request = AsyncMock(return_value='{"success": true}')
    controls = IsgControls(client)
    controls._page = AsyncMock(return_value=number_page(control))
    for value in (31, 22.55, float("nan")):
        with pytest.raises(HomeAssistantError):
            await controls.async_write(control, value)
    client._async_request.assert_not_called()
    with pytest.raises(HomeAssistantError, match="verified"):
        await controls.async_write(control, 22.5)


def test_holiday_date_limits() -> None:
    assert len(HOLIDAY) == 6
    assert parse_control(number_page(HOLIDAY[0], "12"), HOLIDAY[0]) == 12


def radio_page(control: Control, selected: int, options: tuple[str, str]) -> str:
    tab = f"$(\"#subnavactivename\").html('{control.tab}');"
    rows = "".join(
        f'<input type="radio" name="val{control.field}" value="{i}" alt="{label}" '
        f"{'checked' if i == selected else ''}>"
        for i, label in enumerate(options)
    )
    return (
        f'<div id="sub_nav"><div class="main">{control.title}</div></div>'
        f'<script>{tab}</script><form id="werte"><div id="calval{control.field}">'
        f'<h3 class="title">{control.label}</h3>{rows}</div></form>'
    )


async def test_cooling_switch_and_mode_write_verified_values() -> None:
    client = MagicMock(host="isg.local")
    client._async_request = AsyncMock(return_value='{"success": true}')
    controls = IsgControls(client)
    switch = next(c for c in CONTROLS if c.key == "cooling")
    controls._page = AsyncMock(
        side_effect=[radio_page(switch, 0, ("AUS", "EIN")), radio_page(switch, 1, ("AUS", "EIN"))]
    )
    await controls.async_write(switch, True)
    assert json.loads(client._async_request.call_args.kwargs["data"]["data"]) == [
        {"name": "val11042", "value": "1"}
    ]
    select = next(c for c in CONTROLS if c.key == "cooling_2_type")
    options = ("GEBLÄSEKÜHLUNG", "FLÄCHENKÜHLUNG")
    controls._page = AsyncMock(
        side_effect=[radio_page(select, 0, options), radio_page(select, 1, options)]
    )
    await controls.async_write(select, "FLÄCHENKÜHLUNG")
    assert json.loads(client._async_request.call_args.kwargs["data"]["data"]) == [
        {"name": "val11071", "value": "1"}
    ]


async def test_device_rejection_is_not_retried() -> None:
    control = next(c for c in CONTROLS if c.key == "heating_2_comfort")
    client = MagicMock(host="isg.local")
    client._async_request = AsyncMock(return_value='{"success": false}')
    controls = IsgControls(client)
    controls._page = AsyncMock(return_value=number_page(control))
    with pytest.raises(HomeAssistantError, match="did not confirm"):
        await controls.async_write(control, 22.5)
    assert client._async_request.await_count == 1


async def test_auth_failure_cannot_submit_a_write() -> None:
    control = next(c for c in CONTROLS if c.key == "hot_water_comfort")
    client = MagicMock(host="isg.local")
    client._async_fetch_page = AsyncMock(side_effect=StiebelEltronIsgAuthRequiredError())
    client._async_request = AsyncMock()
    with pytest.raises(HomeAssistantError):
        await IsgControls(client).async_write(control, 50.0)
    client._async_request.assert_not_awaited()


async def test_holiday_rejects_invalid_date_range() -> None:
    client = MagicMock(host="isg.local")
    controls = IsgControls(client)
    with pytest.raises(HomeAssistantError):
        await controls.async_set_holiday(date(2027, 5, 1), date(2027, 4, 1))
    client._async_request.assert_not_called()


async def test_holiday_sends_both_dates_and_verifies_readback() -> None:
    client = MagicMock(host="isg.local")
    client._async_request = AsyncMock(return_value='{"success": true}')
    controls = IsgControls(client)
    original_start = "".join(number_page(c, "1") for c in HOLIDAY[:3])
    original_end = "".join(number_page(c, "1") for c in HOLIDAY[3:])
    updated_start = "".join(
        number_page(c, v) for c, v in zip(HOLIDAY[:3], ("3", "5", "27"), strict=True)
    )
    updated_end = "".join(
        number_page(c, v) for c, v in zip(HOLIDAY[3:], ("12", "5", "27"), strict=True)
    )
    controls._page = AsyncMock(
        side_effect=[original_start, original_end, updated_start, updated_end]
    )
    await controls.async_set_holiday(date(2027, 5, 3), date(2027, 5, 12))
    payload = json.loads(client._async_request.call_args.kwargs["data"]["data"])
    assert payload == [
        {"name": "val9", "value": "3"},
        {"name": "val10", "value": "5"},
        {"name": "val11", "value": "27"},
        {"name": "val12", "value": "12"},
        {"name": "val13", "value": "5"},
        {"name": "val14", "value": "27"},
    ]
