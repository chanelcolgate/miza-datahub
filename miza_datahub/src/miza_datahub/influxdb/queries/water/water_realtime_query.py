from typing import Optional

from miza_datahub.services import shift_calendar
from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class WaterRealtimeQuery(InfluxRepository):
    def get_daily_waste_water(self, date: str):
        start, end = shift_calendar.production_day_range(date)
        query = f"""
        SELECT
            SUM("daily_consumption") AS "total_consumption"
        FROM
        (
            SELECT
                sum("hourly_consumption") AS "daily_consumption"
            FROM
            (
                SELECT
                    non_negative_derivative(
                        last("value"),
                        1h
                    ) AS "hourly_consumption"
                FROM "water_measurement"
                WHERE
                (
                    "sub_system" = 'Lưu lượng mương lắng cát'
                    OR "sub_system" = 'Lưu lượng nước giặt mền hệ xeo'
                    OR "sub_system" = 'Lưu lượng nước thải hệ xeo'
                    OR "sub_system" = 'Lưu lượng vi sinh nước thải hệ XLNT'
                )
                    AND time >= '{start.isoformat()}'
                    AND time < '{end.isoformat()}'
                GROUP BY time(1h), "sub_system" fill(none)
            )
            WHERE
                time >= '{start.isoformat()}'
                AND time < '{end.isoformat()}'
            GROUP BY time(1d)
        )
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )

    def get_daily_water_v2(self, date: str):
        start, end = shift_calendar.production_day_range(date)
        query = f"""
        SELECT
            SUM("water_consumption") AS "water_used"
        FROM
        (
            SELECT
                SUM("hourly_consumption") AS "water_consumption"
            FROM (
                SELECT
                    non_negative_derivative(
                        last("value"),
                        1h
                    ) AS "hourly_consumption"
                FROM "water_measurement"
                WHERE
                    "sub_system" = 'Lưu lượng bể 100 m3'
                    AND time >= '{start.isoformat()}'
                    AND time < '{end.isoformat()}'
                GROUP BY time(1h) fill(none)
            )
            WHERE
                time >= '{start.isoformat()}'
                AND time < '{end.isoformat()}'
            GROUP BY time(1d)
        )
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )

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
                AND time < {end_time_str}
            GROUP BY
                time({interval}, 7h),
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
                integral("flow_actual", 1h) as "water_used"
            FROM "miza_realtime"
            WHERE
                "machine" = 'Fresh water'
                AND time >= {start_time_str}
                AND time < {end_time_str}
            {group_by}
            FILL(none)
            TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]
