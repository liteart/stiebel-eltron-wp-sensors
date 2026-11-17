"""Conservative access to the ISG's documented-in-page setting forms."""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup
from homeassistant.exceptions import HomeAssistantError

from .client import StiebelEltronIsgClient, StiebelEltronIsgError


@dataclass(frozen=True, slots=True)
class Control:
    """One field verified against the target device's form."""

    key: str
    page: str
    title: str
    field: str
    label: str
    name: str
    mode: str
    minimum: float = 0
    maximum: float = 0
    step: float = 1
    unit: str | None = None
    tab: str | None = None


CONTROLS = (
    Control(
        "heating_1_comfort",
        "4,2",
        "HEIZEN",
        "10976",
        "KOMFORT TEMPERATUR",
        "Puffer Komforttemperatur",
        "number",
        5,
        30,
        0.1,
        "°C",
        "HEIZKREIS 1",
    ),
    Control(
        "heating_1_eco",
        "4,2",
        "HEIZEN",
        "10977",
        "ECO TEMPERATUR",
        "Puffer Eco-Temperatur",
        "number",
        5,
        30,
        0.1,
        "°C",
        "HEIZKREIS 1",
    ),
    Control(
        "heating_1_curve",
        "4,2",
        "HEIZEN",
        "25",
        "STEIGUNG HEIZKURVE",
        "Puffer Heizkurve",
        "number",
        0,
        3,
        0.01,
        tab="HEIZKREIS 1",
    ),
    Control(
        "heating_2_comfort",
        "4,2,1",
        "HEIZEN",
        "10980",
        "KOMFORT TEMPERATUR",
        "Bodenheizung Komforttemperatur",
        "number",
        5,
        30,
        0.1,
        "°C",
        "HEIZKREIS 2",
    ),
    Control(
        "heating_2_eco",
        "4,2,1",
        "HEIZEN",
        "10981",
        "ECO TEMPERATUR",
        "Bodenheizung Eco-Temperatur",
        "number",
        5,
        30,
        0.1,
        "°C",
        "HEIZKREIS 2",
    ),
    Control(
        "heating_2_max",
        "4,2,1",
        "HEIZEN",
        "10982",
        "MAXIMAL TEMPERATUR",
        "Bodenheizung Maximaltemperatur",
        "number",
        20,
        90,
        0.5,
        "°C",
        "HEIZKREIS 2",
    ),
    Control(
        "heating_2_curve",
        "4,2,1",
        "HEIZEN",
        "26",
        "STEIGUNG HEIZKURVE",
        "Bodenheizung Heizkurve",
        "number",
        0,
        3,
        0.01,
        tab="HEIZKREIS 2",
    ),
    Control(
        "heating_2_room_influence",
        "4,2,1",
        "HEIZEN",
        "10984",
        "RAUMEINFLUSS",
        "Bodenheizung Raumeinfluss",
        "number",
        0,
        100,
        5,
        "%",
        "HEIZKREIS 2",
    ),
    Control(
        "hot_water_comfort",
        "4,3",
        "WARMWASSER",
        "11018",
        "KOMFORT TEMPERATUR",
        "Warmwasser Komforttemperatur",
        "number",
        10,
        60,
        0.1,
        "°C",
        "WARMWASSERTEMPERATUREN",
    ),
    Control(
        "hot_water_eco",
        "4,3",
        "WARMWASSER",
        "11019",
        "ECO TEMPERATUR",
        "Warmwasser Eco-Temperatur",
        "number",
        10,
        60,
        0.1,
        "°C",
        "WARMWASSERTEMPERATUREN",
    ),
    Control(
        "party_hours",
        "3,12",
        "PARTYPROGRAMM",
        "10120",
        "PARTYPROGRAMM",
        "Partyprogramm Dauer",
        "number",
        0,
        24,
        1,
        "h",
    ),
    Control("cooling", "4,8", "KÜHLEN", "11042", "KÜHLEN", "Kühlen", "switch", tab="KÜHLEN"),
    Control(
        "cooling_2",
        "4,8,2",
        "KÜHLEN",
        "11068",
        "KÜHLKREIS",
        "Kühlkreis 2",
        "switch",
        tab="KÜHLKREIS 2",
    ),
    Control(
        "cooling_2_type",
        "4,8,2",
        "KÜHLEN",
        "11071",
        "KÜHLART",
        "Kühlkreis 2 Kühlart",
        "select",
        tab="KÜHLKREIS 2",
    ),
    Control(
        "cooling_2_room",
        "4,8,2",
        "KÜHLEN",
        "11070",
        "RAUMSOLLTEMPERATUR",
        "Kühlkreis 2 Raumsolltemperatur",
        "number",
        20,
        30,
        0.1,
        "°C",
        "KÜHLKREIS 2",
    ),
    Control(
        "cooling_2_curve",
        "4,8,2",
        "KÜHLEN",
        "12040",
        "STEIGUNG KÜHLKURVE",
        "Kühlkreis 2 Kühlkurve",
        "number",
        0,
        3,
        0.05,
        tab="KÜHLKREIS 2",
    ),
    Control(
        "cooling_2_start",
        "4,8,2",
        "KÜHLEN",
        "12041",
        "STARTTEMPERATUR",
        "Kühlkreis 2 Starttemperatur",
        "number",
        15,
        30,
        0.5,
        "°C",
        "KÜHLKREIS 2",
    ),
)

HOLIDAY = (
    Control(
        "holiday_start_day",
        "3,13",
        "FERIENPROGRAMM",
        "9",
        "TAG",
        "",
        "number",
        1,
        31,
        tab="FERIENBEGINN",
    ),
    Control(
        "holiday_start_month",
        "3,13",
        "FERIENPROGRAMM",
        "10",
        "MONAT",
        "",
        "number",
        1,
        12,
        tab="FERIENBEGINN",
    ),
    Control(
        "holiday_start_year",
        "3,13",
        "FERIENPROGRAMM",
        "11",
        "JAHR",
        "",
        "number",
        0,
        99,
        tab="FERIENBEGINN",
    ),
    Control(
        "holiday_end_day",
        "3,13,1",
        "FERIENPROGRAMM",
        "12",
        "TAG",
        "",
        "number",
        1,
        31,
        tab="FERIENENDE",
    ),
    Control(
        "holiday_end_month",
        "3,13,1",
        "FERIENPROGRAMM",
        "13",
        "MONAT",
        "",
        "number",
        1,
        12,
        tab="FERIENENDE",
    ),
    Control(
        "holiday_end_year",
        "3,13,1",
        "FERIENPROGRAMM",
        "14",
        "JAHR",
        "",
        "number",
        0,
        99,
        tab="FERIENENDE",
    ),
)


def parse_control(html: str, control: Control) -> float | bool | str | None:
    """Read a field only when its page, field, label and limits match."""
    soup = BeautifulSoup(html, "html.parser")
    page = soup.select_one("#sub_nav .main")
    if (
        not page
        or page.get_text(" ", strip=True) != control.title
        or not soup.select_one("form#werte")
    ):
        return None
    if control.tab and not re.search(
        r"subnavactivename[^\n]*\.html\(['\"]" + re.escape(control.tab) + r"['\"]\)", html
    ):
        return None
    node = soup.select_one(f"#calval{control.field}")
    heading = node.select_one("h3.title") if node else None
    if not node or not heading or heading.get_text(" ", strip=True) != control.label:
        return None
    name = f"val{control.field}"
    if control.mode == "select":
        choices = node.select(f"input[type=radio][name='{name}']")
        mapping = {x.get("value"): x.get("alt") for x in choices}
        if mapping != {"0": "GEBLÄSEKÜHLUNG", "1": "FLÄCHENKÜHLUNG"}:
            return None
        selected = [x for x in choices if x.has_attr("checked")]
        return selected[0].get("alt") if len(selected) == 1 else None
    if control.mode == "switch":
        choices = node.select(f"input[type=radio][name='{name}']")
        if {x.get("value"): x.get("alt") for x in choices} != {"0": "AUS", "1": "EIN"}:
            return None
        selected = [x for x in choices if x.has_attr("checked")]
        return selected[0].get("value") == "1" if len(selected) == 1 else None
    if node.select_one(f"input[name='{name}'][type=text]") is None:
        return None
    markup = str(node)
    field_pattern = r"valSettings\[['\"]" + name + r"['\"]\]"

    def setting(key: str) -> str | None:
        match = re.search(
            field_pattern + r"\[['\"]" + key + r"['\"]\]\s*=\s*['\"]([^'\"]+)", markup
        )
        return match.group(1) if match else None

    match = re.search(
        r"jsvalues\[['\"]?" + control.field + r"['\"]?\]\[['\"]val['\"]\]\s*=\s*['\"]([^'\"]+)",
        markup,
    )
    step_match = re.search(
        r"change\(['\"]" + name + r"['\"],\s*['\"]\+['\"],\s*[^,]+,\s*[^,]+,\s*['\"]([^'\"]+)",
        markup,
    )
    try:
        if (
            not match
            or not step_match
            or float(step_match.group(1)) != control.step
            or float(setting("min")) != control.minimum
            or float(setting("max")) != control.maximum
        ):
            return None
        value = float(match.group(1).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return value if control.minimum <= value <= control.maximum else None


class IsgControls:
    """Serialize reads and writes to settings, with strict per-device validation."""

    def __init__(self, client: StiebelEltronIsgClient) -> None:
        self.client = client
        self.lock = asyncio.Lock()

    async def _page(self, control: Control) -> str:
        url = f"http://{self.client.host}/?s={control.page}"
        return await self.client._async_fetch_page(
            url, lambda page: parse_control(page, control) is not None
        )

    async def async_read(self) -> dict[str, float | bool | str]:
        """Fetch each settings page once; unsupported fields are omitted."""
        values: dict[str, float | bool | str] = {}
        async with self.lock:
            for page in dict.fromkeys(c.page for c in CONTROLS):
                candidates = [c for c in CONTROLS if c.page == page]
                try:
                    # Any known field establishes page identity; unsupported fields are ignored.
                    url = f"http://{self.client.host}/?s={page}"
                    html = await self.client._async_fetch_page(
                        url,
                        lambda text, choices=candidates: any(
                            parse_control(text, c) is not None for c in choices
                        ),
                    )
                except StiebelEltronIsgError:
                    continue
                for control in candidates:
                    value = parse_control(html, control)
                    if value is not None:
                        values[control.key] = value
        return values

    async def async_write(self, control: Control, value: float | bool | str) -> None:
        """Validate live form, send one setting, and verify its readback."""
        if control not in CONTROLS:
            raise HomeAssistantError("Unknown ISG setting")
        if control.mode == "select":
            mapping = {"GEBLÄSEKÜHLUNG": 0, "FLÄCHENKÜHLUNG": 1}
            if value not in mapping:
                raise HomeAssistantError("Invalid ISG setting value")
            numeric = Decimal(mapping[value])
        else:
            numeric = None
        try:
            if numeric is None:
                numeric = Decimal(str(int(value) if isinstance(value, bool) else value))
            if not numeric.is_finite():
                raise ValueError
            if control.mode == "switch":
                if not isinstance(value, bool):
                    raise ValueError
            elif control.mode == "number" and (
                not (Decimal(str(control.minimum)) <= numeric <= Decimal(str(control.maximum)))
                or ((numeric - Decimal(str(control.minimum))) % Decimal(str(control.step)) != 0)
            ):
                raise ValueError
        except (InvalidOperation, ValueError):
            raise HomeAssistantError("Invalid ISG setting value") from None
        async with self.lock:
            try:
                await self._page(control)
                data = json.dumps(
                    [{"name": f"val{control.field}", "value": str(numeric).replace(".", ",")}]
                )
                answer = await self.client._async_request(
                    "POST", f"http://{self.client.host}/save.php", data={"data": data}
                )
                result = json.loads(answer)
                if (
                    not isinstance(result, dict)
                    or result.get("success") is not True
                    or result.get("warning")
                ):
                    raise HomeAssistantError("ISG did not confirm the change; check the device")
                readback = parse_control(await self._page(control), control)
                if control.mode == "select":
                    verified = readback == value
                else:
                    verified = (
                        readback is not None
                        and Decimal(str(int(readback) if isinstance(readback, bool) else readback))
                        == numeric
                    )
                if not verified:
                    raise HomeAssistantError("ISG change could not be verified; check the device")
            except (StiebelEltronIsgError, ValueError) as err:
                raise HomeAssistantError("ISG operation failed or could not be verified") from err

    async def async_set_holiday(self, start: date, end: date) -> None:
        """Set both holiday dates in one request and verify all six fields."""
        if start > end or not (2000 <= start.year <= 2099 and 2000 <= end.year <= 2099):
            raise HomeAssistantError("Invalid holiday date range")
        numbers = (start.day, start.month, start.year % 100, end.day, end.month, end.year % 100)
        async with self.lock:
            try:
                pages = [await self._page(HOLIDAY[0]), await self._page(HOLIDAY[3])]
                if any(
                    parse_control(pages[0 if i < 3 else 1], c) is None
                    for i, c in enumerate(HOLIDAY)
                ):
                    raise HomeAssistantError("Holiday fields do not match this ISG")
                data = json.dumps(
                    [
                        {"name": f"val{control.field}", "value": str(value)}
                        for control, value in zip(HOLIDAY, numbers, strict=True)
                    ]
                )
                answer = await self.client._async_request(
                    "POST", f"http://{self.client.host}/save.php", data={"data": data}
                )
                result = json.loads(answer)
                if (
                    not isinstance(result, dict)
                    or result.get("success") is not True
                    or result.get("warning")
                ):
                    raise HomeAssistantError(
                        "ISG did not confirm the holiday program; check the device"
                    )
                pages = [await self._page(HOLIDAY[0]), await self._page(HOLIDAY[3])]
                if any(
                    parse_control(pages[0 if i < 3 else 1], c) != numbers[i]
                    for i, c in enumerate(HOLIDAY)
                ):
                    raise HomeAssistantError(
                        "Holiday dates could not be verified; check the device"
                    )
            except (StiebelEltronIsgError, ValueError) as err:
                raise HomeAssistantError("Holiday program failed or could not be verified") from err
