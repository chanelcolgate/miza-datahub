import io
import os

TEMPLATE_PATH = os.path.join(
    "miza_datahub",
    "src",
    "miza_datahub",
    "postgres",
    "migration_template.py",
)


def test_migration_template_contains_expected_tables():
    root = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(root, TEMPLATE_PATH)
    assert os.path.exists(
        template_path
    ), f"Migration template not found at {template_path}"

    content = io.open(template_path, "r", encoding="utf-8").read()
    assert "daily_production_reports" in content
    assert "downtime_events" in content
    assert "create_hypertable" in content
    assert "equipment_id" in content
    assert "machine_code" not in content
    assert "shift_no IN (1, 2)" in content


def test_alembic_revision_uses_equipment_refs():
    root = os.path.dirname(os.path.dirname(__file__))
    revision_path = os.path.join(
        root,
        "miza_datahub",
        "alembic",
        "versions",
        "b7d2e4f6a1c3_add_equipment_refs_and_two_shifts.py",
    )
    assert os.path.exists(revision_path)

    content = io.open(revision_path, "r", encoding="utf-8").read()
    assert "equipment_id" in content
    assert "uk_report_date_shift_equipment" in content
    assert "DROP TABLE" not in content.upper()
    assert 'drop_table("production_shifts")' in content
