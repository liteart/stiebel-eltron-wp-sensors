"""Integration entity mapping tests."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.const import CONF_HOST
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.stiebeleltron_isg.binary_sensor import StiebelEltronIsgBinarySensor
from custom_components.stiebeleltron_isg.const import CONF_SCAN_INTERVAL, CONF_TIMEOUT, DOMAIN
from custom_components.stiebeleltron_isg.scraper import (
    merge_snapshots,
    parse_heat_pump_page,
    parse_info_page,
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
    humidity = StiebelEltronIsgSensor(entry, "raumtemperatur__raumfeuchte_2")
    flow = StiebelEltronIsgSensor(entry, "heizung__volumenstrom")
    status = StiebelEltronIsgBinarySensor(entry, "energiemanagement__deaktiviert")

    assert sensor.native_value == 49.0
    assert sensor.native_unit_of_measurement == "°C"
    assert sensor.device_info["configuration_url"] == f"http://{no_auth_host}/?s=1,1"
    assert starts.native_value == 3287
    assert combined.native_value == 1888.708
    assert combined.native_unit_of_measurement == "kWh"
    assert plant.native_value == 1.92
    assert plant.native_unit_of_measurement == "bar"
    assert humidity.device_class == "humidity"
    assert flow.device_class == "volume_flow_rate"
    assert status.is_on is True


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


async def test_binary_entities_in_home_assistant(hass, heat_pump_page, anlage_page) -> None:
    """Home Assistant creates binary entities with real on/off and unknown states."""
    energy_html = """<table class="info"><tr><th>WÄRMEMENGE</th></tr>
      <tr><td class="key">HEIZEN 1-12 M</td><td class="value">1,057MWh</td></tr></table>"""
    snapshot = merge_snapshots(
        parse_heat_pump_page(heat_pump_page),
        parse_plant_page(anlage_page),
        parse_info_page(energy_html, section_prefix="ENERGIEBILANZ"),
    )
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_HOST: "isg.local"})
    entry.add_to_hass(hass)
    with patch(
        "custom_components.stiebeleltron_isg.client.StiebelEltronIsgClient.async_get_snapshot",
        new=AsyncMock(return_value=snapshot),
    ), patch(
        "custom_components.stiebeleltron_isg.async_get_clientsession", return_value=MagicMock()
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        key = f"{entry.entry_id}_energiemanagement__deaktiviert"
        entity_id = registry.async_get_entity_id("binary_sensor", DOMAIN, key)
        assert entity_id is not None
        assert hass.states.get(entity_id).state == "on"
        assert registry.async_get_entity_id("sensor", DOMAIN, key) is None
        assert "raw_value" not in hass.states.get(entity_id).attributes
        energy_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_energiebilanz_waermemenge__heizen_1_12_m"
        )
        energy = hass.states.get(energy_id)
        assert energy.state == "1057.0"
        assert energy.attributes["device_class"] == "energy"
        assert energy.attributes["unit_of_measurement"] == "kWh"
        assert "state_class" not in energy.attributes
        metric_key = "energiemanagement__deaktiviert"
        coordinator = entry.runtime_data.coordinator
        for value, expected in ((False, "off"), (None, "unknown")):
            snapshot.metrics[metric_key] = replace(snapshot.metrics[metric_key], value=value)
            coordinator.async_set_updated_data(snapshot)
            await hass.async_block_till_done()
            assert hass.states.get(entity_id).state == expected
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_stop(force=True)
