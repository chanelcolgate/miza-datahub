from datetime import date, time, datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError


def test_tc01_create_production_shift(db_session):
    shift_code = "CA_1"
    stmt = sa.text("""
        INSERT INTO production_shifts (shift_code, start_time, end_time)
        VALUES (:code, :start, :end)
        RETURNING shift_id;
    """)
    result = db_session.execute(
        stmt, {"code": shift_code, "start": time(7, 0), "end": time(19, 0)}
    ).fetchone()
    db_session.commit()

    assert result is not None
    assert result[0] is not None


def test_tc02_duplicate_shift_code_fails(db_session):
    """TC-02: Them trùng shift_code phải báo lỗi unique constraint"""
    shift_code = "CA_UNIQUE_TEST"
    stmt = sa.text("""
        INSERT INTO production_shifts (shift_code, start_time, end_time)
        VALUES (:code, :start, :end);
    """)
    db_session.execute(
        stmt, {"code": shift_code, "start": time(7, 0), "end": time(19, 0)}
    )
    db_session.commit()

    # Them lan 2 voi cung ma phai ban IntegrityError
    with pytest.raises(IntegrityError):
        db_session.execute(
            stmt, {"code": shift_code, "start": time(19, 0), "end": time(7, 0)}
        )
        db_session.commit()
    db_session.rollback()


def test_tc03_create_paper_grade(db_session):
    """TC-03: Them moi loai giay san xuat"""
    stmt = sa.text("""
        INSERT INTO paper_grades (code, name, target_gsm)
        VALUES ('TEST-GRADE-01', 'Giấy Test Test', 120.5)
        RETURNING grade_id;
    """)
    res = db_session.execute(stmt).fetchone()
    db_session.commit()
    assert res is not None


def test_tc04_create_equipment(db_session):
    """TC-04: Them moi thiet bi may PM6"""
    stmt = sa.text("""
        INSERT INTO equipment (code, name)
        VALUES ('PM6', 'Máy Xeo Giấy PM6')
        RETURNING equipment_id;
    """)
    res = db_session.execute(stmt).fetchone()
    db_session.commit()
    assert res is not None


def test_tc05_create_crews(db_session):
    """TC-05: Them moi danh muc to truc (A, B, C)"""
    stmt = sa.text("""
        INSERT INTO crews (crew_code, crew_name)
        VALUES ('CREW_A', 'To A')
        RETURNING crew_id;
    """)
    res = db_session.execute(stmt).fetchone()
    db_session.commit()
    assert res is not None


def test_tc06_and_tc07_crew_schedules(db_session):
    """TC-06 & TC-07: Phan cong lich truc
    va kiem tra trung lich (uk_date_shift_crew)"""
    # Tao to truoc
    crew_res = db_session.execute(sa.text("""
            INSERT INTO crews (
                crew_code, crew_name
            ) VALUES (
                'CREW_B', 'To B'
            ) RETURNING crew_id;
        """)).fetchone()
    crew_id = crew_res[0]
    db_session.commit()

    work_date = date(2026, 10, 15)
    shift_no = 1

    # TC-06: Phan cong lich thanh cong
    schedule_stmt = sa.text("""
        INSERT INTO crew_schedules (work_date, shift_no, crew_id)
        VALUES (:w_date, :s_no, :c_id)
    """)
    db_session.execute(
        schedule_stmt, {"w_date": work_date, "s_no": shift_no, "c_id": crew_id}
    )
    db_session.commit()

    # TC-07: Cung ngay va ca do, phan cong to khac phai loi Unique Constraint
    with pytest.raises(IntegrityError):
        db_session.execute(
            schedule_stmt,
            {"w_date": work_date, "s_no": shift_no, "c_id": crew_id},
        )
        db_session.commit()
    db_session.rollback()


def test_tc08_and_tc09_daily_production_reports(db_session):
    """TC-08 & TC-09: Luu bao cao ca/ngay
    va kiem tra rang buoc unique uk_report_date_shift"""
    # Chuan bi du lieu khoa ngoai (Grade va Crew)
    grade_id = db_session.execute(sa.text("""INSERT INTO paper_grades (
                code, name
            ) VALUES (
                'G-REPORT', 'Giay Bao Cao'
            ) RETURNING grade_id;""")).fetchone()[0]
    print(grade_id)

    crew_id = db_session.execute(sa.text("""INSERT INTO crews (
                crew_code, crew_name
            ) VALUES (
                'CREW_C', 'To C'
            ) RETURNING crew_id;""")).fetchone()[0]
    db_session.commit()

    report_date = date(2026, 10, 15)
    shift_no = 1

    # TC-08: Luu bao cao thanh cong voi day du chi so va tu dong gan to
    report_stmt = sa.text("""
        INSERT INTO daily_production_reports (
            report_date, shift_no, grade_id, crew_id,
            actual_production_ton, downtime_hours, production_notes
        ) VALUES (
            :r_date, :s_no, :g_id, :c_id,
            150.5, 1.2, 'Van hanh on dinh'
        )
    """)
    db_session.execute(
        report_stmt,
        {
            "r_date": report_date,
            "s_no": shift_no,
            "g_id": grade_id,
            "c_id": crew_id,
        },
    )
    db_session.commit()

    with pytest.raises(IntegrityError):
        db_session.execute(
            report_stmt,
            {
                "r_date": report_date,
                "s_no": shift_no,
                "g_id": grade_id,
                "c_id": crew_id,
            },
        )
        db_session.commit()
    db_session.rollback()


def test_tc10_downtime_events_hypertable(db_session):
    """TC-10: Luu su kien dung may vao bang TimescaleDB Hypertable"""
    start_t = datetime(2026, 10, 15, 8, 30, tzinfo=timezone.utc)
    end_t = datetime(2026, 10, 15, 8, 55, tzinfo=timezone.utc)

    stmt = sa.text("""
        INSERT INTO downtime_events (
            time, machine_code, start_time, end_time,
            duration_minutes, is_truncated, reason
        ) VALUES (
            :time, :machine, :start, :end, :duration, :truncated, :reason
        ) RETURNING event_id;
    """)

    res = db_session.execute(
        stmt,
        {
            "time": start_t,
            "machine": "PM6",
            "start": start_t,
            "end": end_t,
            "duration": 25.0,
            "truncated": False,
            "reason": "Su co dut giay kho",
        },
    ).fetchone()
    db_session.commit()

    assert res is not None
    assert res[0] is not None
