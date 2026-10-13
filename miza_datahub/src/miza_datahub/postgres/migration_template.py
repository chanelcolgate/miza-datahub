"""Alembic migration template: create daily_production_reports and downtime_events hypertable

This file is a template to be copied into your alembic/versions/ directory as a proper revision file
(or adapted into your project's Alembic environment).

Do NOT run this file directly; create an Alembic revision and paste the upgrade()/downgrade() contents there.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'abc123xyz456'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Enable TimescaleDB extension if not present
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # 2. Create daily_production_reports table
    op.create_table(
        'daily_production_reports',
        sa.Column('report_id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('report_date', sa.Date(), nullable=False),
        sa.Column('shift_no', sa.Integer(), nullable=True),
        sa.Column('grade_id', sa.UUID(), nullable=True),
        sa.Column('actual_production_ton', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('warehouse_in_ton', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('defect_ton', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('total_electricity_kwh', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('spec_electricity', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('total_steam_ton', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('spec_steam', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('total_water_m3', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('spec_water', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('total_pulp_kg', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('spec_pulp', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('run_time_hours', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('downtime_hours', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('availability_rate', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('productivity_tph', sa.Float(), server_default=sa.text('0.0'), nullable=True),
        sa.Column('production_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('report_id'),
        sa.UniqueConstraint('report_date', 'shift_no', name='uk_report_date_shift')
    )
    op.create_index('idx_reports_date', 'daily_production_reports', ['report_date'])

    # 3. Create downtime_events table and convert to TimescaleDB hypertable
    op.create_table(
        'downtime_events',
        sa.Column('event_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('machine_code', sa.String(length=50), server_default=sa.text("'PM6'"), nullable=False),
        sa.Column('start_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('end_time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Float(), nullable=False),
        sa.Column('is_truncated', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.PrimaryKeyConstraint('event_id', 'time')
    )

    # Convert to hypertable
    op.execute("SELECT create_hypertable('downtime_events', 'time', if_not_exists => TRUE);")
    op.create_index('idx_downtime_machine_time', 'downtime_events', ['machine_code', sa.text('time DESC')])


def downgrade() -> None:
    op.drop_table('downtime_events')
    op.drop_table('daily_production_reports')
