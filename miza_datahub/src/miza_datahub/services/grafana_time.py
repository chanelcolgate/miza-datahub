"""
Phân tích time picker của Grafana (from_time / to_time) thành danh sách ngày.

Hỗ trợ:
  - ISO 8601:        2026-09-13T17:00:00.000Z
    (Z/offset được đổi sang giờ VN)
  - YYYY-MM-DD:      2026-10-04
    (from = 00:00, to = 23:59:59.999 giờ VN)
  - epoch ms / s:    1789430400000 | 1789430400
  - tương đối:       now, now-30d, now+1d, now-6h, now-1M, now-1y, now-1Q
  - làm tròn:
    now/d, now-1w/w, now/M, now-1M/M, now/y, now/Q
    (from -> đầu kỳ, to -> cuối kỳ)
  - kết hợp:         now-1d/d+6h, now/M-1d ...
Đơn vị: s m h d w M(tháng) Q(quý) y   (chú ý: m = phút, M = tháng).
"""

import calendar
import re
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Ho_Chi_Minh")
_TOKEN = re.compile(r"\s*(?:([+-])\s*(\d*)\s*(Q|[smhdwMy])|/\s*(Q|[smhdwMy]))")


def _add_months(dt, n):
    y, m = divmod(dt.year * 12 + dt.month - 1 + n, 12)
    m += 1
    return dt.replace(
        year=y, month=m, day=min(dt.day, calendar.monthrange(y, m)[1])
    )


def _add(dt, n, unit):
    if unit == "s":
        return dt + timedelta(seconds=n)
    if unit == "m":
        return dt + timedelta(minutes=n)
    if unit == "h":
        return dt + timedelta(hours=n)
    if unit == "d":
        return dt + timedelta(days=n)
    if unit == "w":
        return dt + timedelta(weeks=n)
    if unit == "M":
        return _add_months(dt, n)
    if unit == "Q":
        return _add_months(dt, 3 * n)
    if unit == "Y":
        return _add_months(dt, 12 * n)
    raise ValueError(f"Đơn vị không hỗ trợ: {unit}")


def _floor(dt, unit, week_start):
    """Đầu kỳ chứa dt. week_start: 0 = thứ Hai, 6 = Chủ nhật."""
    if unit == "s":
        return dt.replace(microsecond=0)
    if unit == "m":
        return dt.replace(second=0, microsecond=0)
    if unit == "h":
        return dt.replace(minute=0, second=0, microsecond=0)
    day0 = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if unit == "d":
        return day0
    if unit == "w":
        return day0 - timedelta(days=(dt.weekday() - week_start) % 7)
    if unit == "M":
        return day0.replace(day=1)
    if unit == "Q":
        return day0.replace(month=(dt.month - 1) // 3 * 3 + 1, day=1)
    if unit == "y":
        return day0.replace(month=1, day=1)
    raise ValueError(f"Đơn vị không hỗ trợ: {unit}")


def _apply_math(dt, rest, is_to, week_start):
    pos = 0
    rest = rest.strip()
    while pos < len(rest):
        m = _TOKEN.match(rest, pos)
        if not m:
            raise ValueError(
                f"Không hiểu biểu thức thời gian: "
                f"'now{rest}' (lỗi tại '{rest[pos:]}')"
            )
        if m.group(1):
            n = int(m.group(2) or 1) * (1 if m.group(1) == "+" else -1)
            dt = _add(dt, n, m.group(3))
        else:
            start = _floor(dt, m.group(4), week_start)
            dt = (
                _add(start, 1, m.group(4)) - timedelta(milliseconds=1)
                if is_to
                else start
            )
        pos = m.end()
    return dt


def parse_grafana_time(expr, *, is_to=False, now=None, tz=TZ, week_start=0):
    """Chuỗi time picker -> datetime có múi giờ `tz`.
    is_to=True thì làm tròn '/x' về CUỐI kỳ."""
    s = str(expr).strip()
    now = (now or datetime.now(tz)).astimezone(tz)
    if s.startswith("now"):
        return _apply_math(now, s[3:], is_to, week_start)
    if s.isdigit():
        n = int(s)
        return datetime.fromtimestamp(
            (n if n >= 10**11 else n * 1000) / 1000, tz
        )
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(f"Không hiểu thời gian: '{expr}'") from e
    if dt.tzinfo is None:  # không có múi giờ -> coi là giờ VN
        dt = dt.replace(tzinfo=tz)
        if is_to and len(s) == 10:  # chỉ có ngày -> hết ngày
            dt = dt.replace(hour=23, minute=59, second=59, microsecond=999000)
    return dt.astimezone(tz)


def resolve_days(from_time, to_time, *, now=None, tz=TZ, week_start=0):
    """
    (from_time, to_time) -> (danh sách ngày giờ VN từ ngày chứa
        from đến ngày chứa to, start, end).
    Nếu `to` rơi đúng 00:00:00.000 thì ngày đó bị loại
        (to coi như hết ngày hôm trước).
    """
    start = parse_grafana_time(
        from_time, is_to=False, now=now, tz=tz, week_start=week_start
    )
    end = parse_grafana_time(
        to_time, is_to=True, now=now, tz=tz, week_start=week_start
    )
    if end < start:
        raise ValueError(f"to_time ({to_time}) nhỏ hơn from_time ({from_time})")
    first, last = start.date(), end.date()
    if end.time() == time(0, 0) and end > start:
        last -= timedelta(days=1)
    days = [first + timedelta(days=i) for i in range((last - first).days + 1)]
    return days, start, end
