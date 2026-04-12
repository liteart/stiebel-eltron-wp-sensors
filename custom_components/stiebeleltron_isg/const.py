"""Constants for the Stiebel Eltron ISG integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "stiebeleltron_isg"
NAME = "Stiebel Eltron ISG Sensory Data READONLY"
PLATFORMS: list[Platform] = [Platform.SENSOR]

DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
DEFAULT_TIMEOUT = 15.0
DEFAULT_SCAN_INTERVAL_MINUTES = int(DEFAULT_SCAN_INTERVAL.total_seconds() / 60)

HEAT_PUMP_URL_PATH = "/?s=1,1"
PLANT_URL_PATH = "/?s=1,0"

CONF_SCAN_INTERVAL = "scan_interval"
CONF_TIMEOUT = "timeout"

MIN_SCAN_INTERVAL = timedelta(minutes=1)
