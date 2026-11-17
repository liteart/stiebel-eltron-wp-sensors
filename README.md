# Stiebel Eltron ISG Sensory Data

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
- Device-validated writable settings for heating, hot water, cooling and programs
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
2. Search for `Stiebel Eltron ISG Sensory Data`.
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

### Changing settings

The integration reads and verifies the specific control fields exposed by the ISG. Matching fields
appear as number, switch, or select entities on the device. Writes are checked against the live form's
page, field identifier, label, limits, and increment; the integration then reads the value back.
Unsupported fields are not exposed. The supported fields are:

- Heating circuit 1 (**Puffer**): comfort and eco temperature, heating-curve slope.
- Heating circuit 2 (**Bodenheizung**): comfort and eco temperature, maximum temperature,
  heating-curve slope and room influence.
- Hot water: comfort and eco temperature.
- Party program: duration from 0 to 24 hours; set 0 to end it.
- Cooling: enable cooling and cooling circuit 2; circuit 2 room target, mode, cooling-curve slope and
  start temperature.

These labels reflect the circuit assignments provided for the original installation; other systems
may use different circuit assignments. Advanced configuration and special on/off temperature fields
are not included. The selected field identifiers and form layout are verified against the original
ISG software version; other versions may expose fewer or no controls.

To set the holiday period, call the Home Assistant action
`stiebeleltron_isg.set_holiday_program`, select any entity of the relevant ISG, and enter start and end
dates. Both dates are sent together and read back. If confirmation or readback fails, check the ISG
interface before retrying: the device might already have applied some or all of the change. The
holiday write was tested with simulated ISG responses, not by changing the physical installation.
Date ranges outside 2000–2099 or with the end before the start are rejected.

### Normalized readings and existing entities

- ISG energy readings are exposed in kWh, with the original numeric value converted from MWh
  where necessary. The ISG's time-window and daily values have no state class: they are not
  cumulative counters suitable for the Energy dashboard.
- Verified on/off indicators, including SG Ready inputs, are binary sensors. Home Assistant
  represents their boolean states as `on` and `off`; unrecognized states are `unknown`.
- An inactive temperature value is `unknown` rather than the text `Aus`. Remaining times are
  duration measurements. Temperature differences in K stay in K and are not absolute temperatures.
- Unknown device-specific values remain text or numbers without inferred units or semantics;
  the integration does not guess the meaning of undocumented operating codes.

### Energy dashboard

Add `VD HEIZEN SUMME (Leistungsaufnahme)` and `VD WARMWASSER SUMME (Leistungsaufnahme)` as
separate individual devices in the Energy dashboard. They expose the ISG's documented cumulative
compressor electricity totals as numeric kWh with `energy` and `total_increasing` classes. These
measure the compressor for heating and hot water, not necessarily the complete installation's
electricity consumption: pumps, controls and electrical backup heating may be excluded. Do not use
heat-output (`WÄRMEMENGE`) sensors as electrical consumption. The ISG values are estimates, not
billing-grade measurements. An external electricity meter is needed for the complete system total.

Values displayed by the ISG as MWh to three decimal places change in steps of 1 kWh after conversion,
so short intervals can appear flat or jump. `TAG` is since midnight; `1-24 h` is an ISG energy-balance
period, not a documented cumulative counter, and its exact period boundary has not been verified.
Home Assistant calculates period usage from changes in each cumulative sensor after it starts
recording, not from the displayed lifetime counter itself.

Older versions exposed derived `GESAMT INKL. HEUTE` sensors that added `TAG` to `SUMME`. These
have been removed because `SUMME` is already a cumulative total and the addition could double-count.
Remove those old sensors from Energy dashboard configuration and select the two `SUMME` sensors;
check existing statistics for incorrect data. Registry entries and historical statistics are not
automatically deleted or corrected.

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
