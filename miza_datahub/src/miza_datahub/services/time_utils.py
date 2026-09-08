from typing import Union, Optional, Tuple
from datetime import datetime, timedelta

import pandas as pd

from miza_datahub.common import config_const as ConfigConst


class TimeUtils:
    @staticmethod
    def to_vn_timestamp(ts: Union[datetime, pd.Timestamp]) -> int:
        if ts is None:
            return 0

        if isinstance(ts, pd.Timestamp):
            ts = ts.to_pydatetime()

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=ConfigConst.VN_TZ)

        return int(ts.timestamp())

    @staticmethod
    def get_production_time_range(
        date: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Tính toán khoảng thời gian (start_time, end_time) theo
        ca kíp nhà máy (6h sáng).
        Trả về: (start_time_str, end_time_sr)
        """
        now_vn = datetime.now(ConfigConst.VN_TZ)
        current_date_real = now_vn.date()

        if date is None:
            date = current_date_real.strftime("%Y-%m-%d")

        input_date = datetime.strptime(date, "%Y-%m-%d").date()

        start_date = input_date
        end_time_str = f"'{date}T06:00:00+07:00' + 1d"

        if input_date == current_date_real:
            if now_vn.hour < 6:
                start_date = input_date - timedelta(days=1)
                end_time_str = (
                    f"'{now_vn.strftime('%Y-%m-%dT%H:%M:%S+07:00')}' - 35m"
                )
            else:
                start_date = input_date
                end_time_str = (
                    f"'{now_vn.strftime('%Y-%m-%dT%H:%M:%S+07:00')}' - 35m"
                )

        start_time_str = f"{start_date.strftime('%Y-%m-%d')}T06:00:00+07:00"

        return start_time_str, end_time_str

    @classmethod
    def date_str_to_vn_timestamp(
        cls, date_str: str, fmt: str = "%d/%m/%Y"
    ) -> int:
        if not date_str or not isinstance(date_str, str):
            return 0

        # Parse string '29/08/2026' -> datetime(2026, 8, 29, 0, 0, 0)
        dt = datetime.strptime(date_str.strip(), fmt)

        return cls.to_vn_timestamp(dt)
