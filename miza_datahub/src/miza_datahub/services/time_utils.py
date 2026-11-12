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
        cls, date_str: str, fmt: str = "%d/%m/%Y", hour: int = 0
    ) -> int:
        if not date_str or not isinstance(date_str, str):
            return 0

        # Parse string '29/08/2026' -> datetime(2026, 8, 29, 0, 0, 0)
        dt = datetime.strptime(date_str.strip(), fmt)
        dt_7am = dt.replace(hour=hour, minute=0, second=0, microsecond=0)

        return cls.to_vn_timestamp(dt_7am)

    @staticmethod
    def calculate_shift_downtime(df_raw, shift_start, shift_end):
        """
        df_raw: DateFrame chứa các mốc thời gian và b_run
                (0: STOP, 1: IDLE, 2: RUN, null: NO_DATA)
        shift_start: datetime (ví dụ: 2026-10-01 07:00:00)
        shift_end: datetime (ví dụ: 2026-10-02 07:00:00)
        """
        if df_raw.empty:
            return pd.DataFrame(
                columns=[
                    "start_time",
                    "end_time",
                    "duration_minutes",
                    "is_truncated",
                ]
            )

        # 1. Sắp xếp dữ liệu theo thời gian
        df = df_raw.sort_values("time").copy()

        # 2. Xử lý giá trị null bằng forward fill (giữ
        # trạng thái gần nhất trước đó)
        df["b_run_filled"] = df["b_run"].ffill()

        # 3. Áp dụng logic trạng thái dừng (Dừng/Nghỉ là 1,
        # Chạy là 0)
        # b_run == 2 -> RUN (0), b_run in [0, 1] hoặc
        # còn null -> STOP (1)
        df["is_stop"] = df["b_run_filled"].apply(lambda x: 0 if x == 2 else 1)

        # 4. Lay điểm dữ liệu ngay trước khi shift_start để
        # xác định chính xác trạng thái lúc đau ca.
        df_before = df[df["time"] < shift_start].tail(1)
        df_in_shift = df[
            (df["time"] >= shift_start) & (df["time"] <= shift_end)
        ]

        df_proc = pd.concat([df_before, df_in_shift]).reset_index(drop=True)

        if df_proc.empty:
            return pd.DataFrame(
                columns=[
                    "start_time",
                    "end_time",
                    "duration_minutes",
                    "is_truncated",
                ]
            )

        # 5. Xác định điểm chuyển đổi trạng thái
        # (1: RUN -> STOP, -1: STOP -> RUN)
        df_proc["change"] = df_proc["is_stop"].diff()

        downtime_events = []

        # Kiểm tra trạng thái tại điểm bắt dau ca
        # (shift_start)
        initial_is_stop = df_proc.iloc[0]["is_stop"]
        in_downtime = initial_is_stop == 1
        event_start = shift_start if in_downtime else None

        # 6. Duyet cac moc thoi gian trong ca
        for _, row in df_proc.iterrows():
            if row["time"] < shift_start:
                continue

            # Chuyen tu RUN -> STOP/IDLE (Bat dau dung)
            if row["change"] == 1:
                in_downtime = True
                event_start = row["time"]

            # Chuyen tu STOP/IDLE -> RUN (Ket thuc dung)
            elif row["change"] == -1 and in_downtime:
                in_downtime = False
                event_end = row["time"]
                duration = (event_end - event_start).total_seconds() / 60.0
                if duration > 0:
                    downtime_events.append(
                        {
                            "start_time": event_start,
                            "end_time": event_end,
                            "duration_minutes": duration,
                            "is_truncated": event_start == shift_start,
                        }
                    )
                event_start = None

        # 7. Nếu đến cuối ca (shift_end) máy van DAN DUNG
        # (chua chuyen ve RUN)
        if in_downtime and event_start is not None:
            event_end = shift_end
            duration = (event_end - event_start).total_seconds() / 60.0
            if duration > 0:
                downtime_events.append(
                    {
                        "start_time": event_start,
                        "end_time": event_end,
                        "duration_minutes": duration,
                        "is_truncated": True,
                    }
                )

        return pd.DataFrame(downtime_events)
