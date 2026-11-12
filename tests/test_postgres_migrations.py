import io
import os
import pytest


def test_migration_template_contains_expected_tables():
    root = os.path.dirname(os.path.dirname(__file__))
    template_path = os.path.join(root, 'postgres', 'migration_template.py')
    assert os.path.exists(template_path), f"Migration template not found at {template_path}"

    content = io.open(template_path, 'r', encoding='utf-8').read()
    assert 'daily_production_reports' in content, 'daily_production_reports not referenced in migration template'
    assert 'downtime_events' in content, 'downtime_events not referenced in migration template'
    assert 'create_hypertable' in content, 'create_hypertable not referenced in migration template'
