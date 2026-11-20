from datetime import date, datetime, timedelta

import pytest

from miza_datahub.common import config_const as ConfigConst
from miza_datahub.services import shift_calendar

DAY = date(2026, 10, 15)
TZ = ConfigConst.VN_TZ


def test_production_day_range_starts_at_seven():
    start, end = shift_calendar.production_day_range(DAY)
    assert start == datetime(2026, 10, 15, 7, tzinfo=TZ)
    assert end == datetime(2026, 10, 16, 7, tzinfo=TZ)


def test_shift_one_runs_seven_to_nineteen():
    start, end = shift_calendar.shift_window(DAY, 1)
    assert start == datetime(2026, 10, 15, 7, tzinfo=TZ)
    assert end == datetime(2026, 10, 15, 19, tzinfo=TZ)


def test_shift_two_runs_nineteen_to_next_seven():
    start, end = shift_calendar.shift_window(DAY, 2)
    assert start == datetime(2026, 10, 15, 19, tzinfo=TZ)
    assert end == datetime(2026, 10, 16, 7, tzinfo=TZ)


def test_none_shift_returns_full_day():
    assert shift_calendar.shift_window(DAY) == (
        shift_calendar.production_day_start(DAY),
        shift_calendar.production_day_end(DAY),
    )


def test_shift_window_strings_keep_offset():
    start, end = shift_calendar.shift_window_strings("2026-10-15", 2)
    assert start == "2026-10-15T19:00:00+07:00"
    assert end == "2026-10-16T07:00:00+07:00"


def test_invalid_shift_raises():
    with pytest.raises(ValueError):
        shift_calendar.shift_window(DAY, 3)


def test_production_day_before_seven_belongs_to_previous_day():
    value = datetime(2026, 10, 15, 6, 59, tzinfo=TZ)
    assert shift_calendar.production_day_for(value) == date(2026, 10, 14)


def test_production_day_at_seven_belongs_to_current_day():
    value = datetime(2026, 10, 15, 7, 0, tzinfo=TZ)
    assert shift_calendar.production_day_for(value) == DAY


def test_production_day_shift_two_belongs_to_start_day():
    value = datetime(2026, 10, 16, 1, 0, tzinfo=TZ)
    assert shift_calendar.production_day_for(value) == DAY


def test_shift_for_boundaries():
    assert shift_calendar.shift_for(datetime(2026, 10, 15, 7, tzinfo=TZ)) == 1
    assert (
        shift_calendar.shift_for(datetime(2026, 10, 15, 18, 59, tzinfo=TZ)) == 1
    )
    assert shift_calendar.shift_for(datetime(2026, 10, 15, 19, tzinfo=TZ)) == 2
    assert (
        shift_calendar.shift_for(datetime(2026, 10, 16, 6, 59, tzinfo=TZ)) == 2
    )


def test_production_month_range_handles_year_end():
    start, end = shift_calendar.production_month_range(2026, 12)
    assert start == datetime(2026, 12, 1, 7, tzinfo=TZ)
    assert end == datetime(2027, 1, 1, 7, tzinfo=TZ)


def test_production_year_range():
    start, end = shift_calendar.production_year_range(2026)
    assert start == datetime(2026, 1, 1, 7, tzinfo=TZ)
    assert end == datetime(2027, 1, 1, 7, tzinfo=TZ)


def test_parse_day_accepts_datetime_and_string():
    assert shift_calendar.parse_day(DAY) == DAY
    assert shift_calendar.parse_day("2026-10-15") == DAY
    assert (
        shift_calendar.parse_day(datetime(2026, 10, 15, 19, tzinfo=TZ)) == DAY
    )


def test_naive_timestamp_is_treated_as_vn_time():
    value = datetime(2026, 10, 16, 1, 0) + timedelta(0)
    assert shift_calendar.production_day_for(value) == DAY
