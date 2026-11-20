from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import Optional, Tuple, Union

from miza_datahub.common import config_const as ConfigConst

PRODUCTION_DAY_START_HOUR = 7
SHIFT_START_HOURS = {1: 7, 2: 19}
SHIFT_END_HOURS = {1: 19, 2: 7}
SHIFT_NUMBERS = (1, 2)

DayLike = Union[date, datetime, str]
TimeRange = Tuple[datetime, datetime]


def parse_day(value: DayLike) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def validate_shift(shift_no: int) -> None:
    if shift_no not in SHIFT_START_HOURS:
        raise ValueError(f"Invalid shift number: {shift_no}. Must be 1 or 2.")


def _at_hour(day: date, hour: int) -> datetime:
    return datetime(
        day.year,
        day.month,
        day.day,
        hour,
        tzinfo=ConfigConst.VN_TZ,
    )


def production_day_start(day: DayLike) -> datetime:
    return _at_hour(parse_day(day), PRODUCTION_DAY_START_HOUR)


def production_day_end(day: DayLike) -> datetime:
    return production_day_start(day) + timedelta(days=1)


def production_day_range(day: DayLike) -> TimeRange:
    return production_day_start(day), production_day_end(day)


def shift_window(day: DayLike, shift_no: Optional[int] = None) -> TimeRange:
    if shift_no is None:
        return production_day_range(day)

    validate_shift(shift_no)
    shift_day = parse_day(day)
    start = _at_hour(shift_day, SHIFT_START_HOURS[shift_no])
    if shift_no == 1:
        return start, _at_hour(shift_day, SHIFT_END_HOURS[shift_no])
    return start, _at_hour(shift_day + timedelta(days=1), 7)


def shift_window_strings(
    day: DayLike, shift_no: Optional[int] = None
) -> Tuple[str, str]:
    start, end = shift_window(day, shift_no)
    return start.isoformat(), end.isoformat()


def production_month_range(year: int, month: int) -> TimeRange:
    if not 1 <= month <= 12:
        raise ValueError(f"Invalid month: {month}")
    start = _at_hour(date(year, month, 1), PRODUCTION_DAY_START_HOUR)
    if month == 12:
        end = _at_hour(date(year + 1, 1, 1), PRODUCTION_DAY_START_HOUR)
    else:
        end = _at_hour(date(year, month + 1, 1), PRODUCTION_DAY_START_HOUR)
    return start, end


def production_year_range(year: int) -> TimeRange:
    start = _at_hour(date(year, 1, 1), PRODUCTION_DAY_START_HOUR)
    end = _at_hour(date(year + 1, 1, 1), PRODUCTION_DAY_START_HOUR)
    return start, end


def production_day_for(value: datetime) -> date:
    if value.tzinfo is None:
        value = value.replace(tzinfo=ConfigConst.VN_TZ)
    else:
        value = value.astimezone(ConfigConst.VN_TZ)

    result = value.date()
    if value.hour < PRODUCTION_DAY_START_HOUR:
        result -= timedelta(days=1)
    return result


def shift_for(value: datetime) -> int:
    if value.tzinfo is None:
        value = value.replace(tzinfo=ConfigConst.VN_TZ)
    else:
        value = value.astimezone(ConfigConst.VN_TZ)

    return 1 if 7 <= value.hour < 19 else 2


def month_days(year: int, month: int) -> int:
    return monthrange(year, month)[1]
