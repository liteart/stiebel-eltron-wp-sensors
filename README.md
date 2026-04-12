# Stiebel Eltron ISG for Home Assistant

Custom Home Assistant integration for Stiebel Eltron heat pumps exposed through the ISG web interface.

The integration always targets the ISG heat pump details page at `http://<host>/?s=1,1`, detects whether the device requires login, optionally submits the configured username and password, and scrapes all visible metrics from the `WÄRMEPUMPE` page into Home Assistant sensors.

## Features

- HACS-compatible custom integration layout
- UI-based setup flow
- Host/IP input plus optional username and password
- Login-page detection and optional authentication
- HTML scraping of the `WÄRMEPUMPE` details page
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
2. Search for `Stiebel Eltron ISG`.
3. Enter:
   - `Host or IP address`
   - `Username` if your ISG login is enabled
   - `Password` if your ISG login is enabled
   - optional polling interval and timeout

Notes:
- The integration builds the target URL as `http://<host>/?s=1,1`.
- If the ISG returns the details page directly, credentials are not required.
- If the ISG returns the login page, the integration posts `make=send`, `user`, and `pass` to the same URL.

## Exposed data

The scraper reads all metrics visible on the `WÄRMEPUMPE` page, including:
- `PROZESSDATEN`
- `WÄRMEMENGE`
- `LEISTUNGSAUFNAHME`
- `LAUFZEIT`
- `STARTS`

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
