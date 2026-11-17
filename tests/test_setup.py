"""Integration entity mapping tests."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from homeassistant.const import CONF_HOST
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stiebeleltron_isg.const import CONF_SCAN_INTERVAL, CONF_TIMEOUT, DOMAIN
from custom_components.stiebeleltron_isg.scraper import (
    merge_snapshots,
    parse_heat_pump_page,
    parse_plant_page,
)
from custom_components.stiebeleltron_isg.sensor import StiebelEltronIsgSensor, async_setup_entry


def test_sensor_entity_maps_snapshot_data(
    heat_pump_page: str,
    anlage_page: str,
    no_auth_host: str,
) -> None:
    """Sensor entities should expose parsed snapshot values and metadata."""
    snapshot = merge_snapshots(
        parse_heat_pump_page(heat_pump_page),
        parse_plant_page(anlage_page),
    )
    coordinator = MagicMock()
    coordinator.data = snapshot
    coordinator.last_update_success = True

    entry = MockConfigEntry(
        domain=DOMAIN,
        title="ISG",
        data={CONF_HOST: no_auth_host},
        options={CONF_SCAN_INTERVAL: 5, CONF_TIMEOUT: 10},
    )
    entry.runtime_data = SimpleNamespace(coordinator=coordinator)

    sensor = StiebelEltronIsgSensor(entry, "prozessdaten__ruecklauftemperatur")
    starts = StiebelEltronIsgSensor(entry, "starts__verdichter")
    combined = StiebelEltronIsgSensor(entry, "leistungsaufnahme__vd_heizen_gesamt_inkl_heute")
    plant = StiebelEltronIsgSensor(entry, "heizung__heizungsdruck")
    status = StiebelEltronIsgSensor(entry, "energiemanagement__deaktiviert")

    assert sensor.native_value == 49.0
    assert sensor.native_unit_of_measurement == "°C"
    assert sensor.device_info["configuration_url"] == f"http://{no_auth_host}/?s=1,1"
    assert starts.native_value == 3287
    assert combined.native_value == 1888.708
    assert combined.native_unit_of_measurement == "kWh"
    assert plant.native_value == 1.92
    assert plant.native_unit_of_measurement == "bar"
    assert status.native_value == "An"


async def test_sensor_availability_and_late_discovery(heat_pump_page: str) -> None:
    """Missing and newly appearing values are handled across updates."""
    snapshot = parse_heat_pump_page(heat_pump_page)
    first_key, second_key = list(snapshot.metrics)[:2]
    readings = dict(snapshot.metrics)
    snapshot.metrics.clear()
    snapshot.metrics[first_key] = readings[first_key]
    coordinator = MagicMock()
    coordinator.data = snapshot
    coordinator.last_update_success = True
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "isg.local"})
    entry.runtime_data = SimpleNamespace(coordinator=coordinator)
    added = []
    await async_setup_entry(MagicMock(), entry, lambda entities: added.extend(entities))
    assert len(added) == 1
    sensor = added[0]
    assert sensor.available
    coordinator.last_update_success = False
    assert not sensor.available
    coordinator.last_update_success = True
    snapshot.metrics.clear()
    assert not sensor.available
    assert sensor.native_value == readings[first_key].value
    snapshot.metrics[second_key] = readings[second_key]
    coordinator.async_add_listener.call_args.args[0]()
    assert len(added) == 2
