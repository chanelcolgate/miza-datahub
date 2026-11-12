# README for postgres migration helpers

This folder contains a migration template and helpers for creating the
Daily Production Reports table and the TimescaleDB hypertable for
Downtime Events.

Instructions:
- Copy the `migration_template.py` contents into a new Alembic revision
  file under `alembic/versions/` (use `alembic revision -m "..."`).
- Adjust `revision` and `down_revision` values as appropriate.
- Run `alembic upgrade head` to apply the migration.
