"""add equipment refs and fixed two-shift constraints

Revision ID: b7d2e4f6a1c3
Revises: c8610998431f
Create Date: 2026-11-18

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b7d2e4f6a1c3"
down_revision: Union[str, Sequence[str], None] = "c8610998431f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "equipment",
        sa.Column("factory_code", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "equipment",
        sa.Column("line_code", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "equipment",
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_equipment_factory_line",
        "equipment",
        ["factory_code", "line_code"],
    )

    op.add_column(
        "daily_production_reports",
        sa.Column(
            "equipment_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "downtime_events",
        sa.Column(
            "equipment_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.execute(
        """
        INSERT INTO equipment (code, name)
        VALUES ('PM6', 'Máy Xeo Giấy PM6')
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(
        """
        INSERT INTO equipment (code, name)
        SELECT DISTINCT machine_code, machine_code
        FROM downtime_events
        WHERE machine_code IS NOT NULL
        ON CONFLICT (code) DO NOTHING
        """
    )
    op.execute(
        """
        UPDATE daily_production_reports
        SET equipment_id = e.equipment_id
        FROM equipment e
        WHERE e.code = 'PM6'
            AND daily_production_reports.equipment_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE downtime_events d
        SET equipment_id = e.equipment_id
        FROM equipment e
        WHERE e.code = d.machine_code
            AND d.equipment_id IS NULL
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM daily_production_reports
                WHERE equipment_id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'daily_production_reports has unmapped equipment_id';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM downtime_events
                WHERE equipment_id IS NULL
            ) THEN
                RAISE EXCEPTION
                    'downtime_events has unmapped equipment_id';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM daily_production_reports
                WHERE shift_no IS NULL OR shift_no NOT IN (1, 2)
            ) THEN
                RAISE EXCEPTION
                    'daily_production_reports has shift_no outside 1..2';
            END IF;
            IF EXISTS (
                SELECT 1
                FROM crew_schedules
                WHERE shift_no NOT IN (1, 2)
            ) THEN
                RAISE EXCEPTION
                    'crew_schedules has shift_no outside 1..2';
            END IF;
        END $$;
        """
    )

    op.alter_column(
        "daily_production_reports",
        "equipment_id",
        nullable=False,
    )
    op.alter_column(
        "downtime_events",
        "equipment_id",
        nullable=False,
    )

    op.drop_constraint(
        "uk_report_date_shift",
        "daily_production_reports",
        type_="unique",
    )
    op.create_unique_constraint(
        "uk_report_date_shift_equipment",
        "daily_production_reports",
        ["report_date", "shift_no", "equipment_id"],
    )
    op.create_check_constraint(
        "ck_dpr_shift_no",
        "daily_production_reports",
        "shift_no IN (1, 2)",
    )
    op.create_check_constraint(
        "ck_crew_schedules_shift_no",
        "crew_schedules",
        "shift_no IN (1, 2)",
    )

    op.execute(
        """
        ALTER TABLE daily_production_reports
        ADD CONSTRAINT fk_dpr_equipment
        FOREIGN KEY (equipment_id)
        REFERENCES equipment (equipment_id)
        ON DELETE RESTRICT
        NOT VALID
        """
    )
    op.execute(
        """
        ALTER TABLE daily_production_reports
        VALIDATE CONSTRAINT fk_dpr_equipment
        """
    )
    op.execute(
        """
        ALTER TABLE downtime_events
        ADD CONSTRAINT fk_downtime_equipment
        FOREIGN KEY (equipment_id)
        REFERENCES equipment (equipment_id)
        ON DELETE RESTRICT
        NOT VALID
        """
    )
    op.execute(
        """
        ALTER TABLE downtime_events
        VALIDATE CONSTRAINT fk_downtime_equipment
        """
    )

    op.create_index(
        "idx_reports_equipment_date",
        "daily_production_reports",
        ["equipment_id", "report_date"],
    )
    op.drop_index(
        "idx_downtime_machine_time",
        table_name="downtime_events",
    )
    op.create_index(
        "idx_downtime_equipment_time",
        "downtime_events",
        ["equipment_id", sa.text("time DESC")],
    )
    op.drop_column("downtime_events", "machine_code")
    op.drop_table("production_shifts")


def downgrade() -> None:
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
    op.add_column(
        "downtime_events",
        sa.Column(
            "machine_code",
            sa.String(length=50),
            server_default="PM6",
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE downtime_events d
        SET machine_code = e.code
        FROM equipment e
        WHERE e.equipment_id = d.equipment_id
        """
    )
    op.drop_index(
        "idx_downtime_equipment_time",
        table_name="downtime_events",
    )
    op.create_index(
        "idx_downtime_machine_time",
        "downtime_events",
        ["machine_code", sa.text("time DESC")],
    )
    op.execute(
        "ALTER TABLE downtime_events DROP CONSTRAINT fk_downtime_equipment"
    )
    op.drop_column("downtime_events", "equipment_id")
    op.drop_index(
        "idx_reports_equipment_date",
        table_name="daily_production_reports",
    )
    op.execute(
        "ALTER TABLE daily_production_reports DROP CONSTRAINT fk_dpr_equipment"
    )
    op.drop_constraint(
        "ck_dpr_shift_no",
        "daily_production_reports",
        type_="check",
    )
    op.drop_constraint(
        "ck_crew_schedules_shift_no",
        "crew_schedules",
        type_="check",
    )
    op.drop_constraint(
        "uk_report_date_shift_equipment",
        "daily_production_reports",
        type_="unique",
    )
    op.create_unique_constraint(
        "uk_report_date_shift",
        "daily_production_reports",
        ["report_date", "shift_no"],
    )
    op.drop_column("daily_production_reports", "equipment_id")
    op.drop_index("idx_equipment_factory_line", table_name="equipment")
    op.drop_column("equipment", "is_active")
    op.drop_column("equipment", "line_code")
    op.drop_column("equipment", "factory_code")
