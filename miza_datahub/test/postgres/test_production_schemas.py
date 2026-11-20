from datetime import date, datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError


def insert_equipment(db_session, code="PM6", name="Máy Xeo Giấy PM6"):
    return db_session.execute(
        sa.text("""
            INSERT INTO equipment (code, name)
            VALUES (:code, :name)
            RETURNING equipment_id;
            """),
        {"code": code, "name": name},
    ).fetchone()[0]


def insert_grade(db_session, code="G-REPORT", name="Giay Bao Cao"):
    return db_session.execute(
        sa.text("""
            INSERT INTO paper_grades (code, name)
            VALUES (:code, :name)
            RETURNING grade_id;
            """),
        {"code": code, "name": name},
    ).fetchone()[0]


def insert_crew(db_session, code="CREW_C", name="To C"):
    return db_session.execute(
        sa.text("""
            INSERT INTO crews (crew_code, crew_name)
            VALUES (:code, :name)
            RETURNING crew_id;
            """),
        {"code": code, "name": name},
    ).fetchone()[0]


def test_create_paper_grade(db_session):
    grade_id = insert_grade(db_session)
    db_session.commit()
    assert grade_id is not None


def test_create_equipment(db_session):
    equipment_id = insert_equipment(db_session)
    db_session.commit()
    assert equipment_id is not None


def test_create_crews(db_session):
    crew_id = insert_crew(db_session)
    db_session.commit()
    assert crew_id is not None


def test_crew_schedule_unique_per_day_and_shift(db_session):
    crew_id = insert_crew(db_session, code="CREW_B", name="To B")
    db_session.commit()

    stmt = sa.text("""
        INSERT INTO crew_schedules (work_date, shift_no, crew_id)
        VALUES (:work_date, :shift_no, :crew_id)
        """)
    params = {
        "work_date": date(2026, 10, 15),
        "shift_no": 1,
        "crew_id": crew_id,
    }
    db_session.execute(stmt, params)
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(stmt, params)
        db_session.commit()
    db_session.rollback()


def test_crew_schedule_rejects_third_shift(db_session):
    crew_id = insert_crew(db_session, code="CREW_D", name="To D")
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(
            sa.text("""
                INSERT INTO crew_schedules (work_date, shift_no, crew_id)
                VALUES (:work_date, :shift_no, :crew_id)
                """),
            {
                "work_date": date(2026, 10, 16),
                "shift_no": 3,
                "crew_id": crew_id,
            },
        )
        db_session.commit()
    db_session.rollback()


def test_daily_report_unique_per_equipment_and_shift(db_session):
    grade_id = insert_grade(db_session)
    crew_id = insert_crew(db_session)
    equipment_id = insert_equipment(db_session)
    db_session.commit()

    stmt = sa.text("""
        INSERT INTO daily_production_reports (
            report_date, shift_no, equipment_id, grade_id, crew_id,
            actual_production_ton, downtime_hours, production_notes
        ) VALUES (
            :report_date, :shift_no, :equipment_id, :grade_id, :crew_id,
            150.5, 1.2, 'Van hanh on dinh'
        )
        """)
    params = {
        "report_date": date(2026, 10, 15),
        "shift_no": 1,
        "equipment_id": equipment_id,
        "grade_id": grade_id,
        "crew_id": crew_id,
    }
    db_session.execute(stmt, params)
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(stmt, params)
        db_session.commit()
    db_session.rollback()


def test_daily_report_allows_second_equipment_same_shift(db_session):
    grade_id = insert_grade(db_session, code="G-REPORT-2")
    crew_id = insert_crew(db_session, code="CREW_E", name="To E")
    equipment_one = insert_equipment(db_session, code="PM3")
    equipment_two = insert_equipment(db_session, code="PM6")
    db_session.commit()

    stmt = sa.text("""
        INSERT INTO daily_production_reports (
            report_date, shift_no, equipment_id, grade_id, crew_id
        ) VALUES (
            :report_date, :shift_no, :equipment_id, :grade_id, :crew_id
        )
        """)
    for equipment_id in (equipment_one, equipment_two):
        db_session.execute(
            stmt,
            {
                "report_date": date(2026, 10, 15),
                "shift_no": 1,
                "equipment_id": equipment_id,
                "grade_id": grade_id,
                "crew_id": crew_id,
            },
        )
    db_session.commit()


def test_daily_report_rejects_third_shift(db_session):
    grade_id = insert_grade(db_session, code="G-REPORT-3")
    crew_id = insert_crew(db_session, code="CREW_F", name="To F")
    equipment_id = insert_equipment(db_session, code="PM3")
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(
            sa.text("""
                INSERT INTO daily_production_reports (
                    report_date, shift_no, equipment_id, grade_id, crew_id
                ) VALUES (
                    :report_date, :shift_no, :equipment_id, :grade_id, :crew_id
                )
                """),
            {
                "report_date": date(2026, 10, 17),
                "shift_no": 3,
                "equipment_id": equipment_id,
                "grade_id": grade_id,
                "crew_id": crew_id,
            },
        )
        db_session.commit()
    db_session.rollback()


def test_downtime_events_use_equipment_id(db_session):
    equipment_id = insert_equipment(db_session)
    db_session.commit()

    start_t = datetime(2026, 10, 15, 8, 30, tzinfo=timezone.utc)
    end_t = datetime(2026, 10, 15, 8, 55, tzinfo=timezone.utc)

    result = db_session.execute(
        sa.text("""
            INSERT INTO downtime_events (
                time, equipment_id, start_time, end_time,
                duration_minutes, is_truncated, reason
            ) VALUES (
                :time, :equipment_id, :start, :end, :duration,
                :truncated, :reason
            ) RETURNING event_id;
            """),
        {
            "time": start_t,
            "equipment_id": equipment_id,
            "start": start_t,
            "end": end_t,
            "duration": 25.0,
            "truncated": False,
            "reason": "Su co dut giay kho",
        },
    ).fetchone()
    db_session.commit()

    assert result is not None
    assert result[0] is not None
