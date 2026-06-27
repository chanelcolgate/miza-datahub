from typing import Optional
from calendar import monthrange

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class WaterRealtimeQuery(InfluxRepository):
    def get_daily_water(self, date: Optional[str] = None, interval: str = "1d"):
        start_time_str, end_time_str = TimeUtils().get_production_time_range(
            date
        )

        query = f"""
            SELECT
                integral("flow_actual", 1h) as "water_used"
            FROM "miza_realtime"
            WHERE
                "machine" = 'Fresh water'
                AND time >= '{start_time_str}'
                AND time <= {end_time_str}
            GROUP BY
                time({interval}, 6h),
                "name"
            FILL(none)
            TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]

    def get_monthly_water(
        self, year: int, month: int | None = None, interval: str = "1d"
    ):
        if month is not None:
            last_day = monthrange(year, month)[1]
            start_time_str = f"'{year}-{month:02d}-01T06:00:00+07:00'"
            end_time_str = (
                f"'{year}-{month:02d}-{last_day}T06:00:00+07:00' + 1d"
            )
        else:
            start_time_str = f"'{year}-01-01T06:00:00+07:00'"
            end_time_str = f"'{year+1}-01-01T06:00:00+07:00'"

        if interval == "1d":
            group_by = f"""
                GROUP BY time({interval}, 6h)
            """
        else:
            group_by = ""

        query = f"""
            SELECT
                integral("flow_actual", 1h) as "water_used"
            FROM "miza_realtime"
            WHERE
                "machine" = 'Fresh water'
                AND time >= {start_time_str}
                AND time <= {end_time_str}
            {group_by}
            FILL(none)
            TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]
