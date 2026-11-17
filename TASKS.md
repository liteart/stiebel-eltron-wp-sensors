### T00 — Documentation bootstrap
- [x] **T00 (DONE)** Create project charter and task tracker  
  **Deliverables**
  - `AGENTS.md` describing project scope, architecture direction, and workflow
  - `TASKS.md` describing tracked implementation tasks with status fields
  **Validation**
  - Documentation exists in the project root
  **Commit**
  - `docs: add project charter and task tracker`

### T01 — Repository bootstrap
- [x] **T01 (DONE)** Initialize git-backed HACS-compatible integration skeleton  
  **Deliverables**
  - git repository initialized for the project
  - `README.md`
  - `.gitignore`
  - `hacs.json`
  - `custom_components/stiebeleltron_isg/` package scaffold
  - `manifest.json`
  **Validation**
  - Repository has the expected top-level structure for a HACS custom integration
  **Commit**
  - `chore: bootstrap hacs integration repository`

### T02 — Constants and config flow
- [x] **T02 (DONE)** Add integration constants and UI-based setup flow  
  **Deliverables**
  - `const.py`
  - `config_flow.py`
  - `strings.json`
  - fields for host/IP, username, and password
  - username and password optional
  **Validation**
  - config flow validates required host input
  - config entry can be created with or without credentials
  **Commit**
  - `feat: add config flow for isg connection settings`

### T03 — Main integration: fetch `?s=1,1`, handle login, and publish all metrics
- [x] **T03 (DONE)** Implement the primary ISG integration flow for the heat pump details page  
  **Deliverables**
  - always build the target URL from the configured host as `http://<host>/?s=1,1`
  - request `?s=1,1` first for every refresh cycle
  - detect whether the response is the login page or the heat pump details page
  - if the login page is returned:
    - submit the login form using the optional configured `user` and `pass` fields
    - preserve session state or cookies as required by the ISG
    - fail with a clear authentication error if credentials are required but missing or invalid
  - if the details page is returned directly:
    - continue without authentication
  - scrape every metric shown on the `WÄRMEPUMPE` page and map it into normalized sensor definitions
  - expose all scraped metrics to Home Assistant as sensors
  **Metric coverage**
  - `PROZESSDATEN`
    - `RÜCKLAUFTEMPERATUR`
    - `VORLAUFTEMPERATUR`
    - `VERDAMPFERTEMPERATUR`
    - `VERDICHTEREINTRITTSTEMPERATUR`
    - `HEISSGASTEMPERATUR`
    - `VERFLÜSSIGERTEMPERATUR`
    - `ÖLSUMPFTEMPERATUR`
    - `DRUCK NIEDERDRUCK`
    - `DRUCK HOCHDRUCK`
    - `WP WASSERVOLUMENSTROM`
    - `STROM INVERTER`
    - `SPANNUNG INVERTER`
    - `ISTDREHZAHL VERDICHTER`
    - `SOLLDREHZAHL VERDICHTER`
    - `RÜCKLAUFTEMPERATUR WÄRMEQUELLE`
    - `VORLAUFTEMPERATUR WÄRMEQUELLE`
    - `WÄRMEQUELLENDRUCK`
    - `LEISTUNG WÄRMEQUELLENPUMPE`
    - `INVERTER AUFNAHMELEISTUNG`
  - `WÄRMEMENGE`
    - `VD HEIZEN TAG`
    - `VD HEIZEN SUMME`
    - `VD WARMWASSER TAG`
    - `VD WARMWASSER SUMME`
    - `NHZ HEIZEN SUMME`
    - `NHZ WARMWASSER SUMME`
  - `LEISTUNGSAUFNAHME`
    - `VD HEIZEN TAG`
    - `VD HEIZEN SUMME`
    - `VD WARMWASSER TAG`
    - `VD WARMWASSER SUMME`
  - `LAUFZEIT`
    - `VD HEIZEN`
    - `VD WARMWASSER`
    - `NHZ 1`
    - `NHZ 2`
    - `NHZ 1/2`
  - `STARTS`
    - `VERDICHTER`
  **Validation**
  - integration works when `?s=1,1` immediately returns the details page
  - integration works when `?s=1,1` first returns the login form and then the details page after authentication
  - the parser extracts values from all tables on the provided `WÄRMEPUMPE` page sample
  - units and numeric values are normalized consistently for Home Assistant sensors
  - missing or changed single fields do not break the full update
  **Commit**
  - `feat: implement main isg heat pump integration flow`

### T04 — HTTP client and auth handling
- [x] **T04 (DONE)** Implement ISG HTTP access with optional authentication  
  **Deliverables**
  - HTTP client module for the ISG web interface
  - support for unauthenticated requests
  - support for optional username/password authentication
  - timeout and connection error handling
  **Validation**
  - request logic behaves correctly for auth and no-auth configurations
  **Commit**
  - `feat: add isg http client with optional authentication`

### T05 — Status page scraper
- [x] **T05 (DONE)** Scrape the ISG status page and normalize fields  
  **Deliverables**
  - scraper module that reads the HTML status page
  - parsing logic for metrics and energy usage fields
  - normalized internal keys for parsed values
  **Validation**
  - parser tests cover representative HTML samples
  - missing fields do not break a full scrape
  **Commit**
  - `feat: add isg status page scraper`

### T06 — Coordinator and data model
- [x] **T06 (DONE)** Add coordinator-driven refresh and structured data mapping  
  **Deliverables**
  - coordinator module
  - refresh interval configuration in code
  - normalized data structure shared by entities
  **Validation**
  - coordinator updates fetch and cache scraper data correctly
  **Commit**
  - `feat: add coordinator for periodic isg updates`

### T07 — Sensor platform
- [x] **T07 (DONE)** Expose scraped metrics as Home Assistant sensors  
  **Deliverables**
  - `sensor.py`
  - sensor descriptions for status and energy metrics
  - availability handling for partial or failed updates
  **Validation**
  - entities map correctly from normalized coordinator data
  **Commit**
  - `feat: expose isg metrics as sensors`

### T08 — Error handling and diagnostics
- [x] **T08 (DONE)** Add robust logging, availability, and diagnostics support  
  **Deliverables**
  - structured log messages for connection and parsing failures
  - sanitized diagnostics support if appropriate
  - no credential leakage in logs
  **Validation**
  - logs remain useful while hiding secrets
  **Commit**
  - `feat: improve error handling and diagnostics`

### T09 — Tests
- [x] **T09 (DONE)** Add automated tests for core integration behavior  
  **Deliverables**
  - parser tests
  - config flow tests
  - coordinator or entity tests where practical
  **Validation**
  - test suite runs successfully
  **Commit**
  - `test: add coverage for scraper and integration setup`

### T10 — Documentation and HACS readiness
- [x] **T10 (DONE)** Finalize documentation and repository metadata  
  **Deliverables**
  - `README.md` usage instructions
  - installation steps for git and HACS
  - configuration notes for authenticated and unauthenticated ISG access
  - repository metadata needed for HACS import
  **Validation**
  - docs describe setup and expected behavior clearly
  **Commit**
  - `docs: document installation and configuration`

### T11 — Energy format validation and derived cumulative electrical totals
- [x] **T11 (DONE)** Validate parsed value formats and add cumulative electrical usage sensors including today  
  **Deliverables**
  - parser coverage proving numeric/unit normalization for representative metric types
  - derived `LEISTUNGSAUFNAHME` metrics for heating and warm water cumulative electrical usage including today
  - Home Assistant sensors automatically exposing the new derived metrics
  **Validation**
  - daily and cumulative electrical usage values are normalized before summing
  - derived heating and warm water totals include both `TAG` and `SUMME`
  - automated tests and a live scrape confirm the resulting values and units
  **Commit**
  - `feat: add derived cumulative electrical usage sensors`

### T12 — Repository sanitization for publication
- [x] **T12 (DONE)** Remove device-specific credentials and private host data from tracked content  
  **Deliverables**
  - scrub any tracked files that contain the private IP or literal credential examples
  - replace sensitive test/example data with neutral placeholders
  - verify the working tree no longer contains the specified secrets
  **Validation**
  - repo-wide search returns no matches for the specified IP or credential strings in tracked files
  - tests still pass after fixture and test-data cleanup
  **Commit**
  - `chore: sanitize repository secrets`

### T13 — Project rename
- [x] **T13 (DONE)** Rename the project display name to `Stiebel Eltron ISG Sensory Data READONLY`
  **Deliverables**
  - update HACS metadata, Home Assistant display metadata, and docs to the new project name
  - keep the integration domain and package path unchanged
  **Validation**
  - the renamed project title is consistent across user-facing metadata
  - tests still pass after the metadata rename
  **Commit**
  - `chore: rename project display metadata`

### T14 — Additional `ANLAGE` page support
- [x] **T14 (DONE)** Fetch and expose metrics from `/?s=1,0` in addition to `/?s=1,1`
  **Deliverables**
  - keep `/?s=1,1` as the initial/authentication entry page
  - fetch `/?s=1,0` with the same authenticated session after login or direct access
  - parse and expose all `ANLAGE` page metrics as Home Assistant sensors
  - preserve existing `WÄRMEPUMPE` metrics and derived totals
  **Validation**
  - automated tests cover the `ANLAGE` page parser and the multi-page client flow
  - a live scrape confirms combined metrics from both pages
  **Commit**
  - `feat: add anlage page scraping`

### T15 — Critical reliability and privacy fixes
- [x] **T15 (DONE)** Correct sensor availability, discovery, timeouts and diagnostics redaction
  **Deliverables**
  - Mark stale or missing sensors unavailable and discover new metrics after refresh
  - Handle request timeouts and redact the host from diagnostics
  **Validation**
  - 15 regression tests pass; Ruff passes
  **Commit**
  - `fix: handle sensor availability and request failures`

### T16 — ISG capabilities and controls
- [ ] **T16 (IN_PROGRESS)** Investigate additional ISG readings and verified writable controls
  **Deliverables**
  - Analyze device pages and document supported settings, including heating circuits
  - Implement verified readings and controls with tests
  **Validation**
  - Verify form details against the target ISG and test without changing device settings
  **Commit**
  - `feat: add verified ISG controls`
  **Investigation so far**
  - Target ISG uses `save.php` with form-encoded JSON; no write has been sent.
  - Heating circuit 1 is the buffer; circuit 2 is the building underfloor heating.
  - The target exposes comfort and eco temperatures, cooling options, a party duration,
    and separate holiday start and end forms. Write verification and entities remain open.

### T17 — Additional information-page sensors
- [x] **T17 (DONE)** Read optional energy balance, plant and heat-pump status and analysis pages
  **Deliverables**
  - Add separate namespaced readings and retain existing sensor identifiers
  - Ignore unavailable optional pages while preserving main readings
  **Validation**
  - 16 tests and Ruff pass; read-only live scrape found 50 additional readings
  **Commit**
  - `feat: expose additional ISG information pages`

### T18 — Normalize Home Assistant readings
- [x] **T18 (DONE)** Normalize measurements and expose binary states as binary sensors
  **Deliverables**
  - Parse verified binary indicators as booleans and expose Home Assistant binary sensors
  - Normalize supported units and distinguish cumulative counters from rolling measurements
  - Preserve unknown values without guessing their meaning and document entity migrations
  **Validation**
  - 19 tests and Ruff pass, including Home Assistant entity and state checks
  - Verified parsing against previously fetched ISG pages: 13 binary states and kWh energy units
  **Commit**
  - `feat: normalize ISG readings for Home Assistant`

### T19 — Reliable Home Assistant energy counters
- [x] **T19 (DONE)** Expose documented cumulative electricity counters without double counting
  **Deliverables**
  - Retire unverified daily-plus-total counters and keep documented compressor totals
  - Keep daily and interval values out of the Energy dashboard
  - Document separate units, counter resolution, scope, and migration
  **Validation**
  - 19 tests and Ruff pass, including numeric HA states, separate °C/%/K/kWh units,
    cumulative counter metadata and a simulated daily reset
  **Commit**
  - `fix: use cumulative ISG energy counters`
