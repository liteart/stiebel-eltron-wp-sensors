# Stiebel Eltron ISG Sensory Data READONLY

Custom Home Assistant integration for Stiebel Eltron heat pumps exposed through the ISG web interface.

The integration always targets the ISG heat pump details page at `http://<host>/?s=1,1`, detects whether the device requires login, optionally submits the configured username and password, and then scrapes metrics from both the `WÄRMEPUMPE` and `ANLAGE` pages into Home Assistant sensors.

## Features

- HACS-compatible custom integration layout
- UI-based setup flow
- Host/IP input plus optional username and password
- Login-page detection and optional authentication
- HTML scraping of the `WÄRMEPUMPE` and `ANLAGE` details pages
- Optional readings from energy balance, plant and heat-pump status, and heat-pump analysis
- Sensor exposure for process data, energy, power consumption, runtime, and starts
- Coordinator-based polling
- Sanitized diagnostics support
- Automated tests for parser, client, config flow, diagnostics, and entity mapping

## Installation

### HACS
1. Add this repository as a custom repository in HACS.
2. Select the repository type `Integration`.
3. Install the integration.
4. Restart Home Assistant.

### Manual
1. Copy `custom_components/stiebeleltron_isg` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.

## Configuration

1. In Home Assistant, open `Settings` -> `Devices & services` -> `Add integration`.
2. Search for `Stiebel Eltron ISG Sensory Data READONLY`.
3. Enter:
   - `Host or IP address`
   - `Username` if your ISG login is enabled
   - `Password` if your ISG login is enabled
   - optional polling interval and timeout

Notes:
- The integration builds the target URL as `http://<host>/?s=1,1`.
- If the ISG returns the details page directly, credentials are not required.
- If the ISG returns the login page, the integration posts `make=send`, `user`, and `pass` to the same URL.
- After access is established, the integration fetches both `/?s=1,1` and `/?s=1,0` with the same session.
- Additional information pages are polled sequentially when available; unsupported pages do not
  prevent the main readings from updating. Available readings depend on the ISG and firmware.

### Normalized readings and existing entities

- ISG energy readings are exposed in kWh, with the original numeric value converted from MWh
  where necessary. Rolling energy-balance intervals have no state class: they are not increasing
  counters, and Home Assistant does not support `measurement` for energy-class sensors.
- Verified on/off indicators, including SG Ready inputs, are binary sensors. Home Assistant
  represents their boolean states as `on` and `off`; unrecognized states are `unknown`.
- An inactive temperature value is `unknown` rather than the text `Aus`. Remaining times are
  duration measurements. Temperature differences in K stay in K and are not absolute temperatures.
- Unknown device-specific values remain text or numbers without inferred units or semantics;
  the integration does not guess the meaning of undocumented operating codes.
- The existing derived electrical totals add `TAG` and `SUMME`; their correctness depends on
  the ISG's `SUMME` excluding the current day. Verify this behavior for your firmware before
  using these derived sensors for billing or the Energy dashboard.

This changes existing on/off entities from `sensor.*` to `binary_sensor.*`. Their old registry
entries and references in automations, dashboards, templates, or scripts are not automatically
migrated; update those references and remove obsolete entries after checking dependencies. Energy
sensor entity IDs remain the same, but their native unit may change from MWh to kWh. Check existing
long-term statistics and Energy dashboard configuration after updating; stored history is not
rewritten by the integration. Restart Home Assistant after installing the update.

## Exposed data

The scraper reads all metrics visible on the `WÄRMEPUMPE` and `ANLAGE` pages, including:
- `PROZESSDATEN`
- `WÄRMEMENGE`
- `LEISTUNGSAUFNAHME`
- `LAUFZEIT`
- `STARTS`
- `RAUMTEMPERATUR`
- `HEIZUNG`
- `WARMWASSER`
- `KÜHLEN`
- `ELEKTRISCHE NACHERWÄRMUNG`
- `ENERGIEMANAGEMENT`

## Development

Create a Python 3.12 virtual environment and install the dev dependencies:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install homeassistant==2025.1.4 pytest-homeassistant-custom-component==0.13.205 pytest==8.3.4 pytest-asyncio==0.24.0 pytest-cov==6.0.0 coverage[toml]==7.6.8 ruff==0.15.10 beautifulsoup4
```

Run validation:

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
```
