from typing import Optional
from calendar import monthrange

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class AirRealtimeQuery(InfluxRepository):
    def get_daily_air(self, date: Optional[str] = None, interval: str = "1d"):
        start_time_str, end_time_str = TimeUtils().get_production_time_range(
            date
        )

        query = f"""
            SELECT
                SUM("steam_used") as "air_used"
            FROM
            (
                SELECT
                    integral("steam_flow",1h) AS "steam_used"
                FROM "miza_realtime"
                WHERE
                    "machine" =~ /^Đường hơi (1|2)$/
                    AND time >= '{start_time_str}'
                    AND time <= {end_time_str}
                GROUP BY
                    time(1h),
                    "machine"::tag
            )
            GROUP BY time({interval}, 6h)
            fill(none)
            TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]

    def get_monthly_air(
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
                SUM("steam_used") as "air_used"
            FROM
            (
                SELECT
                    integral("steam_flow",1h) AS "steam_used"
                FROM "miza_realtime"
                WHERE
                    "machine" =~ /^Đường hơi (1|2)$/
                    AND time >= {start_time_str}
                    AND time <= {end_time_str}
                GROUP BY
                    time(1h),
                    "machine"::tag
            )
            {group_by}
            fill(none)
            TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]
