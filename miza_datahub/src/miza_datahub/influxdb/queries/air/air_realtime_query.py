from miza_datahub.services import shift_calendar
from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class AirRealtimeQuery(InfluxRepository):
    def get_daily_air_v2(self, date: str):
        start, end = shift_calendar.production_day_range(date)
        query = f"""
        SELECT
            SUM("steam_used") as "air_used"
        FROM
        (
            SELECT
                integral("flow_actual",1h) AS "steam_used"
            FROM "dongtien_realtime"
            WHERE
                "machine" = 'Lưu lượng hơi tổng'
                AND time >= '{start.isoformat()}'
                AND time < '{end.isoformat()}'
            GROUP BY time(1d) fill(none)
        )
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )

    def get_daily_air(self, date: str | None = None, interval: str = "1d"):
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
                    AND time < {end_time_str}
                GROUP BY
                    time(1h),
                    "machine"::tag
            )
            GROUP BY time({interval}, 7h)
            fill(none)
            TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]

    def get_monthly_air(
        self, year: int, month: int | None = None, interval: str = "1d"
    ):
        if month is not None:
            start, end = shift_calendar.production_month_range(year, month)
        else:
            start, end = shift_calendar.production_year_range(year)
        start_time_str = f"'{start.isoformat()}'"
        end_time_str = f"'{end.isoformat()}'"

        if interval == "1d":
            group_by = f"""
                GROUP BY time({interval}, 7h)
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
                    AND time < {end_time_str}
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
