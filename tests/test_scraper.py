"""Tests for the ISG scraper."""

from __future__ import annotations

from custom_components.stiebeleltron_isg.scraper import (
    is_heat_pump_page,
    is_login_page,
    is_plant_page,
    merge_snapshots,
    parse_heat_pump_page,
    parse_plant_page,
)


def test_detects_login_page(login_page: str) -> None:
    """The scraper should detect the login page."""
    assert is_login_page(login_page) is True
    assert is_heat_pump_page(login_page) is False
    assert is_plant_page(login_page) is False


def test_parses_heat_pump_page(heat_pump_page: str) -> None:
    """The scraper should extract every metric from the heat pump page."""
    snapshot = parse_heat_pump_page(heat_pump_page)

    assert snapshot.software_version == "v12.2.3"
    assert snapshot.logged_in_user == "demo_user"
    assert snapshot.sections == [
        "PROZESSDATEN",
        "WÄRMEMENGE",
        "LEISTUNGSAUFNAHME",
        "LAUFZEIT",
        "STARTS",
    ]
    assert len(snapshot.metrics) == 37
    assert snapshot.metrics["prozessdaten__ruecklauftemperatur"].value == 49.0
    assert snapshot.metrics["prozessdaten__ruecklauftemperatur"].unit == "°C"
    assert snapshot.metrics["prozessdaten__druck_niederdruck"].value == 6.34
    assert snapshot.metrics["prozessdaten__druck_niederdruck"].unit == "bar"
    assert snapshot.metrics["prozessdaten__wp_wasservolumenstrom"].value == 11.2
    assert snapshot.metrics["prozessdaten__wp_wasservolumenstrom"].unit == "L/min"
    assert snapshot.metrics["prozessdaten__leistung_waermequellenpumpe"].value == 39.8
    assert snapshot.metrics["prozessdaten__leistung_waermequellenpumpe"].unit == "%"
    assert snapshot.metrics["prozessdaten__inverter_aufnahmeleistung"].value == 1.0
    assert snapshot.metrics["prozessdaten__inverter_aufnahmeleistung"].unit == "kW"
    assert snapshot.metrics["leistungsaufnahme__vd_heizen_tag"].value == 0.708
    assert snapshot.metrics["leistungsaufnahme__vd_heizen_tag"].unit == "kWh"
    assert snapshot.metrics["waermemenge__vd_heizen_summe"].value == 16.858
    assert snapshot.metrics["waermemenge__vd_heizen_summe"].unit == "MWh"
    assert snapshot.metrics["laufzeit__vd_heizen"].value == 5436
    assert snapshot.metrics["laufzeit__vd_heizen"].unit == "h"
    assert snapshot.metrics["starts__verdichter"].state_class == "total_increasing"
    assert snapshot.metrics["starts__verdichter"].value == 3287

    heating_total = snapshot.metrics["leistungsaufnahme__vd_heizen_gesamt_inkl_heute"]
    warmwater_total = snapshot.metrics["leistungsaufnahme__vd_warmwasser_gesamt_inkl_heute"]

    assert heating_total.value == 1888.708
    assert heating_total.unit == "kWh"
    assert heating_total.state_class == "total_increasing"
    assert warmwater_total.value == 1747.772
    assert warmwater_total.unit == "kWh"


def test_parses_plant_page(anlage_page: str) -> None:
    """The scraper should extract every metric from the plant page."""
    snapshot = parse_plant_page(anlage_page)

    assert is_plant_page(anlage_page) is True
    assert snapshot.software_version == "v12.2.3"
    assert snapshot.logged_in_user == "demo_user"
    assert snapshot.sections == [
        "RAUMTEMPERATUR",
        "HEIZUNG",
        "WARMWASSER",
        "KÜHLEN",
        "ELEKTRISCHE NACHERWÄRMUNG",
        "ENERGIEMANAGEMENT",
    ]
    assert len(snapshot.metrics) == 30
    assert snapshot.metrics["raumtemperatur__isttemperatur_2"].value == 21.9
    assert snapshot.metrics["raumtemperatur__raumfeuchte_2"].value == 43.6
    assert snapshot.metrics["heizung__heizungsdruck"].value == 1.92
    assert snapshot.metrics["heizung__volumenstrom"].unit == "L/min"
    assert snapshot.metrics["heizung__festwertbetrieb"].value == "Aus"
    assert snapshot.metrics["kuehlen__solltemperatur"].value == "Aus"
    assert snapshot.metrics["energiemanagement__sg_ready_1"].value == 0
    assert snapshot.metrics["energiemanagement__deaktiviert"].value == "An"


def test_merges_heat_pump_and_plant_pages(
    heat_pump_page: str,
    anlage_page: str,
) -> None:
    """The merged snapshot should contain metrics from both pages."""
    snapshot = merge_snapshots(
        parse_heat_pump_page(heat_pump_page),
        parse_plant_page(anlage_page),
    )

    assert len(snapshot.metrics) == 67
    assert snapshot.metrics["starts__verdichter"].value == 3287
    assert snapshot.metrics["heizung__aussentemperatur"].value == 8.9
    assert snapshot.metrics["energiemanagement__deaktiviert"].value == "An"
