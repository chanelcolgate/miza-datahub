# MIZA DataHub

MIZA DataHub is a FastAPI service and Python library for ingesting paper-mill
production workbooks and writing time-series and relational production data.

The repository has two layers:

- Root FastAPI app: `src/app.py`
- Installable library: `miza_datahub/src/miza_datahub/`
- Relational schema and migrations: `miza_datahub/alembic/`

`PLAN.md` is the API modernization roadmap. `AGENTS.md` contains repository
operating instructions.

## Domain model

```mermaid
classDiagram
    DailyProductionReport "0..*" --> "1" Equipment : produced on
    DailyProductionReport "0..*" --> "1" PaperGrade : classified as
    DailyProductionReport "0..*" --> "1" Crew : produced by
    CrewSchedule "0..*" --> "1" Crew : assigned to
    DowntimeEvent "0..*" --> "1" Equipment : affects

    class Equipment {
      equipmentId
      code
      name
      factoryCode
      lineCode
      isActive
    }
    class DailyProductionReport {
      reportId
      reportDate
      shiftNo
      equipmentId
      gradeId
      crewId
    }
    class DowntimeEvent {
      eventId
      time
      equipmentId
      startTime
      endTime
      durationMinutes
    }
    class CrewSchedule {
      scheduleId
      workDate
      shiftNo
      crewId
    }
    class PaperGrade
    class Crew
```

Key rules:

- `Equipment` is the managed catalog. `factoryCode` and `lineCode` are fields,
  not separate entities.
- `DailyProductionReport` is one machine for one production day and shift. Its
  unique key is `(report_date, shift_no, equipment_id)`.
- `DowntimeEvent` is independent of reports. It references `Equipment` and is
  aggregated by equipment plus production day/shift.
- Catalogs are referenced by ID with `ON DELETE RESTRICT`; history must survive
  catalog retirement.
- There is no `ProductionShift` table.

## Production day and shifts

All production-day calculations use one rule:

- Timezone: `Asia/Ho_Chi_Minh`
- Production day starts: `07:00`
- Shift 1: `07:00-19:00`
- Shift 2: `19:00-07:00` on the next calendar day

The shared implementation is
`miza_datahub/src/miza_datahub/services/shift_calendar.py`. Use it instead of
hard-coded `06:00`, `07:00`, or `6h` offsets.

A shift-2 record belongs to the production day on which it starts. For example,
`2026-10-15` shift 2 runs from `2026-10-15T19:00` to `2026-10-16T07:00` and is
stored with `report_date = 2026-10-15`.

## Setup

Python 3.11 is required.

```bash
uv sync
uv pip install -e miza_datahub
```

Or run the app without installing the library:

```bash
PYTHONPATH=miza_datahub/src uv run uvicorn src.app:app --reload
```

Do not use `miza_datahub/requirements.txt`; it is stale.

## Database migrations

The Postgres/TimescaleDB schema is managed by Alembic from `miza_datahub/`.

```bash
cd miza_datahub
alembic upgrade head
```

The migration requires the TimescaleDB extension. The latest revision adds
`equipment_id` references to production facts, introduces the fixed two-shift
checks, removes `production_shifts`, and replaces `machine_code` on downtime
events with `equipment_id`.

Existing daily reports without a machine reference are backfilled to `PM6`.
Review the migration preflight before running it against production data:
rows with null/invalid `shift_no` or unmapped downtime equipment will stop the
migration.

## Tests

Run verification in this order from `miza_datahub/`:

```bash
tox -e format
tox -e lint
tox -e typecheck
tox -e py311
```

`tox -e py311` only runs the live DongTien query test. To run a specific test,
use the tox environment directly:

```bash
.tox/py311/bin/pytest test/services/test_shift_calendar.py
.tox/py311/bin/pytest test/postgres/test_production_schemas.py
```

The suite is integration-oriented. It expects live InfluxDB, Postgres/
TimescaleDB, and Selenium/Edge for scraper tests. `test/conftest.py` defaults to:

- InfluxDB: `localhost:8090/dongtien`
- Postgres/TimescaleDB: `postgresql+psycopg2://odoo:odoo@localhost:32768/monitoring`

Run `alembic upgrade head` before the schema tests. Files named `*_ignore.py`
are skipped.

## API status

The current FastAPI surface is `POST /excel/read`, `POST /excel/upload`, and
`GET /daily` in `src/app.py`. The versioned `/v1` contract, authentication,
idempotent imports, and queue-backed workers are planned in `PLAN.md`.

The Postgres report writer in
`miza_datahub/src/miza_datahub/postgres/writers/daily_production_reports.py` is
kept and tested, but is not wired into the FastAPI app.

## Data compatibility notes

- New electricity shift writes use the `Tổng Ca 7h` tag. The Influx query
  accepts both `Tổng Ca 6h` and `Tổng Ca 7h` for transition data.
- Moving from the legacy `06:00` production day to `07:00` changes historical
  attribution for electricity, air, water, pulp, and OEE queries. Validate
  dashboards and historical comparisons before deploying.
- Downtime migration creates equipment rows for existing `machine_code` values
  so foreign keys can be applied. Curate the resulting catalog after migration.

## Known sharp edges

- `detect_file_types` returns `ValueError(...)` instead of raising it, so
  `ReaderFactory.create` can return `None` for unknown files.
- `OEEService.calculate_pq` still overwrites the supplied quality DataFrame and
  zeroes Q.
- Legacy `06:00` offsets and `Tổng Ca 6h` data remain in historical series.
