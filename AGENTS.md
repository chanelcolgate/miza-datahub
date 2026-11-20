# AGENTS.md

## What this repo is

Two layers with separate manifests/locks:

- Root: FastAPI web app, entrypoint `src/app.py` (imports the library below).
- `miza_datahub/`: distributable library (`src/miza_datahub/`) with its own
  `pyproject.toml`, `setup.cfg` (setuptools + tox), `uv.lock`, fixtures in
  `miza_datahub/data/`. It is NOT a uv workspace of the root. It also contains
  InfluxDB, TimescaleDB/Postgres, and Selenium/EVNSPC scraping code.

`PLAN.md` is the current API modernization roadmap.
`doc/ARCHITECTURE_IMPLEMENTATION_PLAN.md` is the original proposal, not the
implementation. `main.py` is boilerplate, not the app entrypoint.

## Setup / run

- Python 3.11 (`.python-version`, CI, tox all pin it).
- Root deps: `uv sync` (FastAPI, pandas, SQLAlchemy, psycopg).
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
tox -e py311       # one live-Influx test, not the full suite
```

- `tox -e py311` runs only
  `test/influxdb/queries/oee/test_dongtien_realtime_query.py`; the other
  pytest targets in `setup.cfg` are commented out.
- `test/conftest.py` skips every `*_ignore.py` test.
- Tox has no `{posargs}`, so extra args after `--` are ignored (including CI's
  `--cov` flags). Run pytest from the tox env to target a test:

```bash
.tox/py311/bin/pytest test/services/test_grafana_time.py::TestResolveDays::test_iso_utc_cua_grafana
```

Windows uses `.tox\py311\Scripts\pytest`. Run `tox -e py311` once to create
the env.

Order matters when verifying: format -> lint -> typecheck -> py311. CI
(`.github/workflows/miza_datahub.yml`) runs these same tox envs, is
`workflow_dispatch` only, and publishes on `v*` tags.

## Testing quirks

- The real suite is `miza_datahub/test/`. Root
  `tests/test_postgres_migrations.py` checks the template at
  `miza_datahub/src/miza_datahub/postgres/migration_template.py`.
- Tests are integration tests, not hermetic unit tests. `conftest.py` defaults
  to live Influx at `localhost:8090/dongtien`, Postgres/TimescaleDB at
  `postgresql+psycopg2://odoo:odoo@localhost:32768/monitoring`, and Selenium
  Edge plus `ddddocr` for scraper tests. No services are mocked.
- Postgres schema tests assume migrations exist; run `alembic upgrade head`
  from `miza_datahub/` first (see `miza_datahub/README.md`). The migration
  requires the TimescaleDB extension.
- `PostgresRepository` builds `postgresql+psycopg` URLs while `conftest.py` and
  `alembic.ini` use `psycopg2`; both drivers are referenced.
- Workbook fixtures (`Q.xlsx`, `OEE.xlsx`, `Air.xlsx`, `DT.xlsx`) are used only
  by `test_reader_factory_ignore.py`, which is skipped.

## Config

- `ConfigUtil` (singleton) reads `./config/miza_datahub_config.props` relative
  to CWD. No sample is tracked (`*.props` is gitignored); a missing file is
  reported as "loaded" and silently falls back to defaults.
- Sections: `[Influx]`, `[TimescaleDB]`, `[Postgres]`, `[Selenium]`,
  `[Telegram]`, `[Reports]`.
- `BaseReader` defaults Influx to `192.168.10.2:8090/miza_new` and TimescaleDB
  to `192.168.10.2:5432/monitoring` (odoo/odoo); `conftest.py` defaults to
  `localhost:8090/dongtien` and `localhost:32768/monitoring`.
- Telegram `file_id` readers require a `token` in `[Telegram]`.

## Architecture notes

- Flow: FastAPI endpoint -> `ReaderFactory.create` -> `BaseReader` (fetches
  bytes from Telegram `file_id` or local path, builds an Influx client, loads
  TimescaleDB settings) -> analyzer `.load()` -> `.write()` -> Influx line
  protocol and/or Postgres.
- File detection is by Excel sheet name: `OEE` -> oee,
  `Chi_Tiet_Chat_Luong` -> quality, `3_ĐKSX_OK` -> plan, `Báo cáo hơi` -> air,
  `TH` -> dt.
- Production-day rules live in `services/shift_calendar.py`: the day starts at
  `07:00`, shift 1 is `07:00-19:00`, and shift 2 is `19:00-07:00` next day.
  Use it instead of hard-coded `06:00`, `07:00`, or `6h` offsets.
- Domain model: `Equipment` (with `factory_code`/`line_code` value fields),
  `PaperGrade`, `Crew`, `CrewSchedule`, `DailyProductionReport`, and
  `DowntimeEvent`. Reports and downtime reference `equipment_id`; downtime is
  independent and aggregated by equipment plus production day/shift. There is
  no `ProductionShift` table.
- `QualityAnalyzer` computes P/Q by querying actual/plan production from Influx
  before writing.
- `InfluxRepository` now provides line-protocol/metric helpers
  (`_build_line_protocol`, `_safe_divide`, `_write_metrics_for_dates`,
  `extract_single_value`); queries are still hand-built InfluxQL f-strings.

## Known broken / sharp edges

- `detect_file_types` returns `ValueError(...)` instead of raising it, so
  `ReaderFactory.create` can return `None` for unknown files.
- `OEEService.calculate_pq` still overwrites the passed quality DataFrame with
  an empty one, zeroing Q, even with its newer `mode` argument.
- The Postgres report writer is kept and updated, but is still not wired into
  the FastAPI app. `PLAN.md` tracks that decision.
- Legacy Influx electricity data uses the `Tổng Ca 6h` tag; new writes use
  `Tổng Ca 7h`, and the query accepts both during the transition.

## Conventions

- Commits must follow Conventional Commits: commitlint runs via
  `.husky/commit-msg`. `.husky/pre-commit` only runs `npm test`, which is a
  no-op.
- Black line length is 80 (`miza_datahub/pyproject.toml`); flake8 max is 80.
  Do not add comments; match the existing minimal style.
