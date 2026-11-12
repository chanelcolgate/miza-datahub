from typing import Optional
from calendar import monthrange

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class WaterRealtimeQuery(InfluxRepository):
    def get_daily_waste_water(self, date: str):
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
                    AND time >= '{date}T07:00:00+07:00'
                    AND time <= '{date}T07:00:00+07:00' + 1d
                GROUP BY time(1h), "sub_system" fill(none)
            )
            WHERE
                time >= '{date}T07:00:00+07:00'
                AND time <= '{date}T07:00:00+07:00' + 1d
            GROUP BY time(1d)
        )
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )

    def get_daily_water_v2(self, date: str):
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
                    AND time >= '{date}T07:00:00+07:00'
                    AND time <= '{date}T07:00:00+07:00' + 1d
                GROUP BY time(1h) fill(none)
            )
            WHERE
                time >= '{date}T07:00:00+07:00'
                AND time <= '{date}T07:00:00+07:00' + 1d
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
