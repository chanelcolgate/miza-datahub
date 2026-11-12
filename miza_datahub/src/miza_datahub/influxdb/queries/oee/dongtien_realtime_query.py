from typing import Optional
from datetime import datetime, timedelta

import pandas as pd

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
        base_dt = datetime.strptime(date, "%Y-%m-%d")
        next_date = (base_dt + timedelta(days=1)).strftime("%Y-%m-%d")

        if shift == 1:
            start_str = f"{date}T07:00:00+07:00"
            end_str = f"{date}T19:00:00+07:00"
            shift_start = pd.Timestamp(f"{date} 07:00:00")
            shift_end = pd.Timestamp(f"{date} 19:00:00")
        elif shift == 2:
            start_str = f"{date}T19:00:00+07:00"
            end_str = f"{next_date}T07:00:00+07:00"
            shift_start = pd.Timestamp(f"{date} 19:00:00")
            shift_end = pd.Timestamp(f"{next_date} 07:00:00")
        else:
            start_str = f"{date}T07:00:00+07:00"
            end_str = f"{next_date}T07:00:00+07:00"
            shift_start = pd.Timestamp(f"{date} 07:00:00")
            shift_end = pd.Timestamp(f"{next_date} 07:00:00")
        query = f"""
        SELECT last("b_run") AS "b_run"
        FROM "dongtien_realtime"
        WHERE "machine" = 'PM6'
            AND time >= '{start_str}' - 5m
            AND time <= '{end_str}'
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
