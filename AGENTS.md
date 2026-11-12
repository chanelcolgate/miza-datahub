# AGENTS.md

## What this repo is

Two layers with separate manifests/locks:

- Root: FastAPI web app, entrypoint `src/app.py` (imports the library below).
- `miza_datahub/`: distributable library (`src/miza_datahub/`) with its own
  `pyproject.toml`, `setup.cfg` (setuptools + tox), `uv.lock`, fixtures in
  `miza_datahub/data/`. It is NOT a uv workspace of the root.

`doc/ARCHITECTURE_IMPLEMENTATION_PLAN.md` is a proposal, not the current
implementation. `main.py` is boilerplate, not the app entrypoint.

## Setup / run

- Python 3.11 (`.python-version`, CI, tox all pin it).
- Root deps: `uv sync`.
- The app needs the nested package importable; either
  `uv pip install -e miza_datahub` or run with
  `PYTHONPATH=miza_datahub/src uv run uvicorn src.app:app --reload`.
- Do not use `miza_datahub/requirements.txt` for setup: it is stale/generated
  and contains a commented absolute editable path from another machine.

## Verification (run inside `miza_datahub/`)

```bash
tox -e format      # black --check --diff src test
tox -e lint        # flake8 (max 80, ignores E203,W503)
tox -e typecheck   # black check + mypy src test
tox -e py311       # pytest
```

Single test (tox changes CWD to `miza_datahub/`):

```bash
tox -e py311 -- test/services/test_reader_factory.py::test_excel_1
```

Order matters when verifying: format -> lint -> typecheck -> py311. CI
(`.github/workflows/miza_datahub.yml`) runs these same tox envs, is
`workflow_dispatch` only, and publishes on `v*` tags.

## Testing quirks

- All Python tests live under `miza_datahub/test/`; the root has none.
- Tests are integration tests, not hermetic unit tests. They read
  `data/Q.xlsx` / `data/OEE.xlsx` via `Path("data")` (CWD-relative) and write
  to a live InfluxDB. Run from `miza_datahub/`, not the repo root, or fixtures
  are not found.
- No services are mocked; expect tests to need network access to InfluxDB.

## Config

- `ConfigUtil` (singleton) reads `./config/miza_datahub_config.props` relative
  to CWD. No sample is tracked (`*.props` is gitignored); a missing file is
  reported as "loaded" and silently falls back to defaults.
- Influx defaults: host `192.168.10.2`, port `8090`, db `miza_new`.
- Telegram `file_id` readers require a `token` in the `[Telegram]` section.

## Architecture notes

- Flow: FastAPI endpoint -> `ReaderFactory.create` -> `BaseReader` (fetches
  bytes from Telegram `file_id` or local path, always builds an Influx client)
  -> `OEEAnalyzer`/`QualityAnalyzer.load()` -> `.write()` -> Influx line
  protocol via `PaperDailyOEEWriter`.
- File type is detected by Excel sheet name: `OEE` or `Chi_Tiet_Chat_Luong`.
- Production day is shift-based: day starts 06:00; Influx queries use
  `Asia/Ho_Chi_Minh`. Preserve these conventions in calculations.
- `QualityAnalyzer` computes P/Q by querying actual/plan production from Influx
  before writing.
- All queries are hand-built InfluxQL f-strings; `InfluxRepository` only
  provides escape/lifecycle helpers.

## Known broken / sharp edges

- `miza_datahub/src/miza_datahub/postgres/writers/daily_production_reports.py`
  imports modules and `config_const` names that do not exist; do not import it
  or assume it works. It is not wired into the app.
- `detect_file_types` returns `ValueError(...)` instead of raising it, so
  `ReaderFactory.create` can return `None` for unknown files.
- `OEEService.calculate_pq` currently overwrites the passed quality DataFrame
  with an empty one, zeroing the Q column.

## Conventions

- Commits must follow Conventional Commits: commitlint runs via
  `.husky/commit-msg`. `.husky/pre-commit` only runs `npm test`, which is a
  no-op.
- Black line length is 80 (`miza_datahub/pyproject.toml`); flake8 max is 80.
  Do not add comments; match the existing minimal style.
