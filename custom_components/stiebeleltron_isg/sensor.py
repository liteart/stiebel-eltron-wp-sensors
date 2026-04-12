"""Sensor platform for Stiebel Eltron ISG."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import StiebelEltronIsgConfigEntry
from .const import DOMAIN, HEAT_PUMP_URL_PATH, NAME
from .scraper import (
    KIND_CURRENT,
    KIND_DURATION,
    KIND_ENERGY,
    KIND_FREQUENCY,
    KIND_POWER,
    KIND_PRESSURE,
    KIND_TEMPERATURE,
    KIND_VOLTAGE,
    STATE_MEASUREMENT,
    STATE_TOTAL_INCREASING,
    MetricReading,
)

UNIT_MAP = {
    "°C": UnitOfTemperature.CELSIUS,
    "A": UnitOfElectricCurrent.AMPERE,
    "V": UnitOfElectricPotential.VOLT,
    "kWh": UnitOfEnergy.KILO_WATT_HOUR,
    "MWh": UnitOfEnergy.MEGA_WATT_HOUR,
    "Hz": UnitOfFrequency.HERTZ,
    "kW": UnitOfPower.KILO_WATT,
    "%": PERCENTAGE,
    "h": UnitOfTime.HOURS,
    "bar": "bar",
    "L/min": "L/min",
}

DEVICE_CLASS_MAP = {
    KIND_CURRENT: SensorDeviceClass.CURRENT,
    KIND_DURATION: SensorDeviceClass.DURATION,
    KIND_ENERGY: SensorDeviceClass.ENERGY,
    KIND_FREQUENCY: SensorDeviceClass.FREQUENCY,
    KIND_POWER: SensorDeviceClass.POWER,
    KIND_PRESSURE: SensorDeviceClass.PRESSURE,
    KIND_TEMPERATURE: SensorDeviceClass.TEMPERATURE,
    KIND_VOLTAGE: SensorDeviceClass.VOLTAGE,
}

STATE_CLASS_MAP = {
    STATE_MEASUREMENT: SensorStateClass.MEASUREMENT,
    "total": SensorStateClass.TOTAL,
    STATE_TOTAL_INCREASING: SensorStateClass.TOTAL_INCREASING,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: StiebelEltronIsgConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor entities from a config entry."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        StiebelEltronIsgSensor(entry, metric.key)
        for metric in coordinator.data.metrics.values()
    )


class StiebelEltronIsgSensor(CoordinatorEntity, SensorEntity):
    """Representation of a single ISG metric."""

    _attr_has_entity_name = True

    def __init__(self, entry: StiebelEltronIsgConfigEntry, metric_key: str) -> None:
        """Initialize the sensor."""
        super().__init__(entry.runtime_data.coordinator)
        self._entry = entry
        self._metric_key = metric_key
        metric = self.metric
        self._attr_unique_id = f"{entry.entry_id}_{metric.key}"
        self._attr_name = f"{metric.label} ({metric.section.title()})"
        self._attr_suggested_display_precision = metric.suggested_display_precision
        self._attr_entity_registry_enabled_default = True

    @property
    def metric(self) -> MetricReading:
        """Return the current metric from coordinator data."""
        return self.coordinator.data.metrics[self._metric_key]

    @property
    def native_value(self):
        """Return the current sensor value."""
        return self.metric.value

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the normalized native unit."""
        return UNIT_MAP.get(self.metric.unit, self.metric.unit)

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return the Home Assistant device class."""
        return DEVICE_CLASS_MAP.get(self.metric.kind)

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return the Home Assistant state class."""
        return STATE_CLASS_MAP.get(self.metric.state_class)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return static metadata for the metric."""
        return {
            "section": self.metric.section,
            "label": self.metric.label,
            "raw_value": self.metric.raw_value,
        }

    @property
    def available(self) -> bool:
        """Return availability of the entity."""
        return self._metric_key in self.coordinator.data.metrics

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information for the ISG."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title or NAME,
            manufacturer="Stiebel Eltron",
            model="ISG",
            sw_version=self.coordinator.data.software_version,
            configuration_url=f"http://{self._entry.data['host']}{HEAT_PUMP_URL_PATH}",
        )
