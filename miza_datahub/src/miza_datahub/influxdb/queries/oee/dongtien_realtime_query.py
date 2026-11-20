from typing import Optional

import pandas as pd

from miza_datahub.services import shift_calendar
from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class DongTienRealtimeQuery(InfluxRepository):
    def get_shift_status(self, date: str, shift: Optional[int] = None):
        """
        Query dữ liệu trạng thái chạy/dừng máy (b_run)
        từ InfluxDB.

        :param date: Chuỗi ngày định dạng 'YYYY-MM-DD'
        (vd: '2026-10-07')
        :param shift: 1 (Ca 1: 07:00-19:00), 2
        (Ca 2: 19:00-07:00 ngày hôm sau),
        None (Cả ngày: 07:00-07:00)
        """
        start_dt, end_dt = shift_calendar.shift_window(date, shift)
        start_str = start_dt.isoformat()
        end_str = end_dt.isoformat()
        shift_start = pd.Timestamp(start_dt).tz_localize(None)
        shift_end = pd.Timestamp(end_dt).tz_localize(None)
        query = f"""
        SELECT last("b_run") AS "b_run"
        FROM "dongtien_realtime"
        WHERE "machine" = 'PM6'
            AND time >= '{start_str}' - 5m
            AND time < '{end_str}'
        GROUP BY time(1m) fill(previous)
        """
        try:
            values = (
                self.query(query)["results"][0]
                .get("series", [{}])[0]
                .get("values", [])
            )
        except (KeyError, IndexError, TypeError):
            values = []

        df_raw = pd.DataFrame(values, columns=["time", "b_run"])
        df_raw["time"] = (
            pd.to_datetime(df_raw["time"])
            .dt.tz_convert("Asia/Ho_Chi_Minh")
            .dt.tz_localize(None)
        )

        result = TimeUtils.calculate_shift_downtime(
            df_raw, shift_start, shift_end
        )
        return result
