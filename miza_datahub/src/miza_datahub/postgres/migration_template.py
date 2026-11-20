"""Alembic migration template for production fact tables.

This template assumes the catalog tables created by revision
``c8610998431f`` already exist: ``equipment``, ``paper_grades``, and
``crews``. Copy the ``upgrade()``/``downgrade()`` bodies into a new
Alembic revision; do not run this file directly.

The production day starts at 07:00 Asia/Ho_Chi_Minh and has two shifts:
``1`` = 07:00-19:00, ``2`` = 19:00-07:00 on the next calendar day.
"""

from alembic import op  # type: ignore[attr-defined]
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "abc123xyz456"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    op.create_table(
        "daily_production_reports",
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("shift_no", sa.Integer(), nullable=False),
        sa.Column(
            "equipment_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("crew_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "actual_production_ton",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "warehouse_in_ton",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "defect_ton",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "total_electricity_kwh",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "spec_electricity",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "total_steam_ton",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "spec_steam",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "total_water_m3",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "spec_water",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "total_pulp_kg",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "spec_pulp",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "run_time_hours",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "downtime_hours",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "availability_rate",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column(
            "productivity_tph",
            sa.Float(),
            server_default=sa.text("0.0"),
            nullable=True,
        ),
        sa.Column("production_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("report_id"),
        sa.CheckConstraint("shift_no IN (1, 2)", name="ck_dpr_shift_no"),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipment.equipment_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["paper_grades.grade_id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["crew_id"],
            ["crews.crew_id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "report_date",
            "shift_no",
            "equipment_id",
            name="uk_report_date_shift_equipment",
        ),
    )
    op.create_index(
        "idx_reports_equipment_date",
        "daily_production_reports",
        ["equipment_id", "report_date"],
    )

    op.create_table(
        "downtime_events",
        sa.Column(
            "event_id", sa.BigInteger(), autoincrement=True, nullable=False
        ),
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "equipment_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column("start_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("end_time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Float(), nullable=False),
        sa.Column(
            "is_truncated", sa.Boolean(), server_default="false", nullable=True
        ),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("event_id", "time"),
        sa.ForeignKeyConstraint(
            ["equipment_id"],
            ["equipment.equipment_id"],
            ondelete="RESTRICT",
        ),
    )

    op.execute(
        "SELECT create_hypertable('downtime_events', 'time', "
        "if_not_exists => TRUE);"
    )
    op.create_index(
        "idx_downtime_equipment_time",
        "downtime_events",
        ["equipment_id", sa.text("time DESC")],
    )


def downgrade() -> None:
    op.drop_index("idx_downtime_equipment_time", table_name="downtime_events")
    op.execute(
        "SELECT drop_hypertable('downtime_events', cascade_drop => TRUE);"
    )
    op.drop_table("downtime_events")
    op.drop_index(
        "idx_reports_equipment_date", table_name="daily_production_reports"
    )
    op.drop_table("daily_production_reports")
