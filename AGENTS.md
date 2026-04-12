# AGENTS.md — Home Assistant Stiebel Eltron ISG Scraper Integration

## Project definition
**Project name:** `homeassistant-stiebeleltron-scraper-plugin`  
**Primary goal:** Build a HACS-compatible Home Assistant custom integration in Python for Stiebel Eltron heat pumps that connect through the ISG web interface.

The integration must:
- be installable from a git repository and through HACS
- use the standard Home Assistant custom integration layout
- collect values from the Stiebel Eltron ISG status page with a simple web scraper
- expose status, metrics, and energy usage values as Home Assistant sensors
- accept the ISG IP/host, optional username, and optional password through the Home Assistant UI
- support both authenticated and unauthenticated ISG setups

---

## Functional scope

### Required functionality
1. Create a Home Assistant custom integration under `custom_components/`.
2. Implement UI-based setup with a config flow.
3. Allow the user to enter:
   - ISG IP address or hostname
   - username (optional)
   - password (optional)
4. Fetch the ISG status page over HTTP(S).
5. Scrape and normalize relevant values from the HTML page.
6. Expose parsed values as Home Assistant sensor entities.
7. Refresh values on a scheduled interval using Home Assistant patterns.
8. Handle connection, auth, parsing, and availability errors cleanly.

### Initial non-goals
- Direct device control through the ISG
- Cloud connectivity
- Firmware-specific reverse engineering beyond the visible status page
- Complex browser automation; use a simple scraper only

---

## Technical direction

### Integration shape
- Python-based Home Assistant custom integration
- HACS-compatible repository structure
- Expected core files include:
  - `custom_components/stiebeleltron_isg/__init__.py`
  - `custom_components/stiebeleltron_isg/manifest.json`
  - `custom_components/stiebeleltron_isg/config_flow.py`
  - `custom_components/stiebeleltron_isg/coordinator.py`
  - `custom_components/stiebeleltron_isg/sensor.py`
  - `custom_components/stiebeleltron_isg/const.py`
  - `custom_components/stiebeleltron_isg/scraper.py`
  - `custom_components/stiebeleltron_isg/strings.json`
  - `hacs.json`
  - `README.md`

### Implementation principles
- Prefer simple, readable Python over heavy abstractions.
- Keep scraping logic isolated from Home Assistant entity logic.
- Normalize raw scraped labels into stable internal field keys.
- Use `DataUpdateCoordinator` for polling and refresh management.
- Treat authentication as optional and attempt requests accordingly.
- Fail soft when individual fields are missing; do not break the whole update.

### Scraping rules
- Use a lightweight HTTP client and HTML parser.
- Do not require JavaScript execution.
- Build parsing against stable labels or table structures where possible.
- Keep metric extraction declarative so new fields can be added safely.

---

## Repository workflow

### Source of truth
- `TASKS.md` is the execution plan for the project.
- Implementation work must follow the tasks listed in `TASKS.md`.
- If a new task is discovered, add it to `TASKS.md` before or during implementation.

### Task status rules
Every task in `TASKS.md` must:
- be written in Markdown
- have an ID
- include a status in its title

Allowed statuses:
- `OPEN`
- `IN_PROGRESS`
- `BLOCKED`
- `DONE`

Required workflow:
1. Before starting a task, change its status to `IN_PROGRESS`.
2. If blocked, change its status to `BLOCKED` and note the reason.
3. When finished, change its status to `DONE`.
4. Keep deliverables, validation notes, and commit message suggestions in the task entry.

### Commit rules
After finishing each task:
1. stage all changed files
2. create a git commit for that task
3. use a focused commit message that matches the completed work

Do not leave completed task work uncommitted.

---

## Quality bar

Each implementation task should aim to include:
- clear separation between HTTP fetching, scraping, and entity mapping
- type hints for non-trivial Python modules
- logging for operational failures without leaking credentials
- tests where practical for parsing and config flow behavior
- documentation updates when user-facing behavior changes

### Definition of done
A task is done when:
- the code or documentation for the task is complete
- related task status in `TASKS.md` is updated
- basic validation for the task has been performed
- all changed files are staged and committed to git

---

## Expected implementation phases
- Bootstrap the HACS-compatible repository structure
- Add Home Assistant metadata and config flow
- Implement HTTP access with optional authentication
- Implement ISG page scraping and field normalization
- Wire scraped data into coordinator-driven sensor entities
- Add tests and documentation

---

## Notes for future work
- Keep sensor naming stable once released.
- Treat the ISG HTML as potentially inconsistent across installations.
- Prefer conservative parsing with explicit fallbacks over brittle shortcuts.
- Keep credentials out of logs, diagnostics, and exceptions.
