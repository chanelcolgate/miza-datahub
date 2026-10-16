"""create daily production reports and downtime events hypertable

Revision ID: c8610998431f
Revises:
Create Date: 2026-10-13 04:20:25.641600

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c8610998431f"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Kích hoạt extension TimescaleDB (nếu chưa có)
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    # 2. Tạo bảng danh mục ProductionShift
    op.create_table(
        "production_shifts",
        sa.Column(
            "shift_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("shift_code", sa.String(length=20), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("shift_id"),
        sa.UniqueConstraint("shift_code"),
    )

    # 3. Tạo bảng danh mục PaperGrade
    op.create_table(
        "paper_grades",
        sa.Column(
            "grade_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("target_gsm", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("grade_id"),
        sa.UniqueConstraint("code"),
    )

    # 4. Tạo bảng danh mục Equipment
    op.create_table(
        "equipment",
        sa.Column(
            "equipment_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("equipment_id"),
        sa.UniqueConstraint("code"),
    )

    # 5. Tạo bảng danh mục Tổ trực (Crews: A, B, C)
    op.create_table(
        "crews",
        sa.Column(
            "crew_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("crew_code", sa.String(length=20), nullable=False),
        sa.Column("crew_name", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("crew_id"),
        sa.UniqueConstraint("crew_code"),
    )

    # 6. Tạo bảng Lịch trực xoay vòng (CrewSchedules) - Quản việc tổ nào trực ca vào ngày nào
    op.create_table(
        "crew_schedules",
        sa.Column(
            "schedule_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("shift_no", sa.Integer(), nullable=False),
        sa.Column("crew_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("schedule_id"),
        sa.ForeignKeyConstraint(
            ["crew_id"],
            ["crews.crew_id"],
        ),
        sa.UniqueConstraint("work_date", "shift_no", name="uk_date_shift_crew"),
    )
    op.create_index("idx_crew_schedules_date", "crew_schedules", ["work_date"])

    # 2. Tạo bảng daily_production_reports
    op.create_table(
        "daily_production_reports",
        sa.Column(
            "report_id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("shift_no", sa.Integer(), nullable=True),
        sa.Column("grade_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("crew_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "actual_production_ton",
            sa.Float(),
            server_default="0.0",
            nullable=True,
        ),
        sa.Column(
            "warehouse_in_ton", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "defect_ton", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "total_electricity_kwh",
            sa.Float(),
            server_default="0.0",
            nullable=True,
        ),
        sa.Column(
            "spec_electricity", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "total_steam_ton", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "spec_steam", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "total_water_m3", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "spec_water", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "total_pulp_kg", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column("spec_pulp", sa.Float(), server_default="0.0", nullable=True),
        sa.Column(
            "run_time_hours", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "downtime_hours", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "availability_rate", sa.Float(), server_default="0.0", nullable=True
        ),
        sa.Column(
            "productivity_tph", sa.Float(), server_default="0.0", nullable=True
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
        sa.ForeignKeyConstraint(
            ["grade_id"],
            ["paper_grades.grade_id"],
        ),
        sa.ForeignKeyConstraint(
            ["crew_id"],
            ["crews.crew_id"],
        ),
        sa.UniqueConstraint(
            "report_date", "shift_no", name="uk_report_date_shift"
        ),
    )
    op.create_index(
        "idx_reports_date", "daily_production_reports", ["report_date"]
    )

    # 3. Tạo bảng downtime_events và chuyển thành TimescaleDB Hypertable
    op.create_table(
        "downtime_events",
        sa.Column(
            "event_id", sa.BigInteger(), autoincrement=True, nullable=False
        ),
        sa.Column("time", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column(
            "machine_code",
            sa.String(length=50),
            server_default="PM6",
            nullable=False,
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
    )

    # Chuyển thành TimescaleDB Hypertable
    op.execute(
        "SELECT create_hypertable('downtime_events', 'time', if_not_exists => TRUE);"
    )
    op.create_index(
        "idx_downtime_machine_time",
        "downtime_events",
        ["machine_code", sa.text("time DESC")],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_downtime_machine_time", table_name="downtime_events")

    op.execute(
        "SELECT drop_hypertable('downtime_events', cascade_drop => TRUE);"
    )
    op.drop_table("downtime_events")

    op.drop_index("idx_reports_date", table_name="daily_production_reports")
    op.drop_table("daily_production_reports")

    op.drop_index("idx_crew_schedules_date", table_name="crew_schedules")
    op.drop_table("crew_schedules")

    op.drop_table("crews")
    op.drop_table("equipment")
    op.drop_table("paper_grades")
    op.drop_table("production_shifts")
