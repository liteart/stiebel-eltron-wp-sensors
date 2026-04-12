"""HTML scraper for the Stiebel Eltron ISG heat pump page."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup, Tag

METRIC_VALUE_RE = re.compile(r"^\s*([-+]?\d+(?:[.,]\d+)?)\s*([^\d\s].*)?\s*$")
ENERGY_TO_KWH = {
    "kWh": 1.0,
    "MWh": 1000.0,
}

KIND_TEMPERATURE = "temperature"
KIND_PRESSURE = "pressure"
KIND_FLOW = "flow"
KIND_CURRENT = "current"
KIND_VOLTAGE = "voltage"
KIND_FREQUENCY = "frequency"
KIND_PERCENTAGE = "percentage"
KIND_POWER = "power"
KIND_ENERGY = "energy"
KIND_DURATION = "duration"
KIND_COUNT = "count"

STATE_MEASUREMENT = "measurement"
STATE_TOTAL_INCREASING = "total_increasing"


@dataclass(slots=True, frozen=True)
class MetricReading:
    """Parsed metric from the ISG page."""

    key: str
    section: str
    label: str
    raw_value: str
    value: Any
    unit: str | None
    kind: str | None
    state_class: str | None
    suggested_display_precision: int | None


@dataclass(slots=True, frozen=True)
class IntegrationSnapshot:
    """Parsed snapshot of the ISG heat pump page."""

    metrics: dict[str, MetricReading]
    sections: list[str]
    software_version: str | None
    logged_in_user: str | None


def is_login_page(html: str) -> bool:
    """Return whether the page is the ISG login page."""
    soup = BeautifulSoup(html, "html.parser")
    login_screen = soup.select_one("#loginscreen")
    return login_screen is not None and login_screen.select_one("input[name='user']") is not None


def is_heat_pump_page(html: str) -> bool:
    """Return whether the page contains the heat pump data tables."""
    soup = BeautifulSoup(html, "html.parser")
    return _is_info_page(soup, "WÄRMEPUMPE")


def is_plant_page(html: str) -> bool:
    """Return whether the page contains the plant data tables."""
    soup = BeautifulSoup(html, "html.parser")
    return _is_info_page(soup, "ANLAGE")


def parse_heat_pump_page(html: str) -> IntegrationSnapshot:
    """Parse the ISG heat pump page."""
    snapshot = parse_info_page(html, expected_page_name="WÄRMEPUMPE")
    metrics = dict(snapshot.metrics)
    _add_derived_energy_metrics(metrics)
    return IntegrationSnapshot(
        metrics=metrics,
        sections=snapshot.sections,
        software_version=snapshot.software_version,
        logged_in_user=snapshot.logged_in_user,
    )


def parse_plant_page(html: str) -> IntegrationSnapshot:
    """Parse the ISG plant page."""
    return parse_info_page(html, expected_page_name="ANLAGE")


def parse_info_page(html: str, *, expected_page_name: str | None = None) -> IntegrationSnapshot:
    """Parse a generic ISG info page with metric tables."""
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.select("table.info")
    if not tables:
        raise ValueError("No metric tables found")
    if expected_page_name and not _is_info_page(soup, expected_page_name):
        raise ValueError(f"Expected ISG page {expected_page_name}")

    metrics: dict[str, MetricReading] = {}
    sections: list[str] = []
    for table in tables:
        heading = table.select_one("th")
        if heading is None:
            continue
        section = _clean_label(heading.get_text(" ", strip=True))
        sections.append(section)

        for row in table.select("tr"):
            key_cell = row.select_one("td.key")
            value_cell = row.select_one("td.value")
            if key_cell is None or value_cell is None:
                continue

            label = _clean_label(key_cell.get_text(" ", strip=True))
            raw_value = _extract_value_cell(value_cell)
            key = _normalize_key(section, label)
            metrics[key] = MetricReading(
                key=key,
                section=section,
                label=label,
                raw_value=raw_value,
                **_parse_metric_payload(section, label, raw_value),
            )

    if not metrics:
        raise ValueError("No metrics parsed from info page")

    return IntegrationSnapshot(
        metrics=metrics,
        sections=sections,
        software_version=_optional_text(soup.select_one("#versionsNummer")),
        logged_in_user=_optional_text(soup.select_one("#login strong")),
    )


def merge_snapshots(*snapshots: IntegrationSnapshot) -> IntegrationSnapshot:
    """Merge multiple page snapshots into one integration snapshot."""
    metrics: dict[str, MetricReading] = {}
    sections: list[str] = []
    software_version: str | None = None
    logged_in_user: str | None = None

    for snapshot in snapshots:
        metrics.update(snapshot.metrics)
        for section in snapshot.sections:
            if section not in sections:
                sections.append(section)
        if software_version is None:
            software_version = snapshot.software_version
        if logged_in_user is None:
            logged_in_user = snapshot.logged_in_user

    return IntegrationSnapshot(
        metrics=metrics,
        sections=sections,
        software_version=software_version,
        logged_in_user=logged_in_user,
    )


def _parse_metric_payload(section: str, label: str, raw_value: str) -> dict[str, Any]:
    """Parse a raw metric value."""
    match = METRIC_VALUE_RE.match(raw_value)
    if not match:
        return {
            "value": raw_value,
            "unit": None,
            "kind": None,
            "state_class": None,
            "suggested_display_precision": None,
        }

    value_token = match.group(1).replace(",", ".")
    unit = _normalize_unit(match.group(2))

    value: int | float
    if "." in value_token:
        value = float(value_token)
        precision = len(value_token.split(".", maxsplit=1)[1])
    else:
        value = int(value_token)
        precision = 0

    kind = _infer_kind(label, unit)
    state_class = _infer_state_class(section, label, kind)
    return {
        "value": value,
        "unit": unit,
        "kind": kind,
        "state_class": state_class,
        "suggested_display_precision": precision or None,
    }


def _extract_value_cell(cell: Tag) -> str:
    """Extract a stable value representation from a table cell."""
    text = cell.get_text(" ", strip=True)
    if text:
        return text

    image = cell.select_one("img")
    if image is None:
        return ""

    src = image.get("src", "")
    lower_src = src.lower()
    if "_an" in lower_src:
        return "An"
    if "_aus" in lower_src:
        return "Aus"
    alt = image.get("alt", "")
    return _clean_label(alt) or src


def _add_derived_energy_metrics(metrics: dict[str, MetricReading]) -> None:
    """Add derived cumulative electrical-usage metrics."""
    _add_combined_energy_metric(
        metrics,
        section="LEISTUNGSAUFNAHME",
        daily_label="VD HEIZEN TAG",
        cumulative_label="VD HEIZEN SUMME",
        derived_label="VD HEIZEN GESAMT INKL. HEUTE",
    )
    _add_combined_energy_metric(
        metrics,
        section="LEISTUNGSAUFNAHME",
        daily_label="VD WARMWASSER TAG",
        cumulative_label="VD WARMWASSER SUMME",
        derived_label="VD WARMWASSER GESAMT INKL. HEUTE",
    )


def _add_combined_energy_metric(
    metrics: dict[str, MetricReading],
    *,
    section: str,
    daily_label: str,
    cumulative_label: str,
    derived_label: str,
) -> None:
    """Add a cumulative energy metric that includes the current day."""
    daily_metric = metrics.get(_normalize_key(section, daily_label))
    cumulative_metric = metrics.get(_normalize_key(section, cumulative_label))
    if daily_metric is None or cumulative_metric is None:
        return

    daily_value = _convert_energy_to_kwh(daily_metric)
    cumulative_value = _convert_energy_to_kwh(cumulative_metric)
    if daily_value is None or cumulative_value is None:
        return

    key = _normalize_key(section, derived_label)
    metrics[key] = MetricReading(
        key=key,
        section=section,
        label=derived_label,
        raw_value=f"{cumulative_metric.raw_value} + {daily_metric.raw_value}",
        value=round(cumulative_value + daily_value, 3),
        unit="kWh",
        kind=KIND_ENERGY,
        state_class=STATE_TOTAL_INCREASING,
        suggested_display_precision=3,
    )


def _convert_energy_to_kwh(metric: MetricReading) -> float | None:
    """Convert an energy metric to kWh."""
    factor = ENERGY_TO_KWH.get(metric.unit or "")
    if factor is None:
        return None
    return float(metric.value) * factor


def _infer_kind(label: str, unit: str | None) -> str | None:
    """Infer the metric kind from the unit and label."""
    if unit == "°C":
        return KIND_TEMPERATURE
    if unit == "bar":
        return KIND_PRESSURE
    if unit == "L/min":
        return KIND_FLOW
    if unit == "A":
        return KIND_CURRENT
    if unit == "V":
        return KIND_VOLTAGE
    if unit == "Hz":
        return KIND_FREQUENCY
    if unit == "%":
        return KIND_PERCENTAGE
    if unit == "kW":
        return KIND_POWER
    if unit in {"kWh", "MWh"}:
        return KIND_ENERGY
    if unit == "h":
        return KIND_DURATION
    if unit is None and "START" in label:
        return KIND_COUNT
    if label == "VERDICHTER":
        return KIND_COUNT
    return None


def _infer_state_class(section: str, label: str, kind: str | None) -> str | None:
    """Infer the Home Assistant state class equivalent."""
    upper_label = label.upper()
    upper_section = section.upper()

    if kind in {
        KIND_TEMPERATURE,
        KIND_PRESSURE,
        KIND_FLOW,
        KIND_CURRENT,
        KIND_VOLTAGE,
        KIND_FREQUENCY,
        KIND_PERCENTAGE,
        KIND_POWER,
    }:
        return STATE_MEASUREMENT

    if kind == KIND_ENERGY and "SUMME" in upper_label:
        return STATE_TOTAL_INCREASING
    if kind == KIND_ENERGY:
        return "total"

    if kind in {KIND_DURATION, KIND_COUNT}:
        return STATE_TOTAL_INCREASING

    if upper_section == "STARTS":
        return STATE_TOTAL_INCREASING

    return None


def _normalize_key(section: str, label: str) -> str:
    """Normalize a section + label combination to a stable key."""
    return f"{_slug(section)}__{_slug(label)}"


def _slug(text: str) -> str:
    """Create a predictable ASCII key."""
    normalized = text.lower()
    replacements = {
        "ä": "ae",
        "ö": "oe",
        "ü": "ue",
        "ß": "ss",
        "/": "_",
    }
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def _normalize_unit(unit: str | None) -> str | None:
    """Normalize a raw unit string."""
    if unit is None:
        return None
    compact = unit.strip().replace(" ", "")
    replacements = {
        "l/min": "L/min",
        "KWh": "kWh",
        "MWh": "MWh",
    }
    return replacements.get(compact, compact)


def _clean_label(text: str) -> str:
    """Normalize whitespace in visible labels."""
    return re.sub(r"\s+", " ", text).strip()


def _optional_text(element: Any) -> str | None:
    """Return stripped text from a BeautifulSoup node."""
    if element is None:
        return None
    text = element.get_text(" ", strip=True)
    return text or None


def _is_info_page(soup: BeautifulSoup, page_name: str) -> bool:
    """Return whether the page contains the expected info view."""
    sub_nav = soup.select_one("#sub_nav")
    if not bool(soup.select("table.info td.key")) or sub_nav is None:
        return False
    title = _optional_text(sub_nav.select_one(".main"))
    return title == page_name
