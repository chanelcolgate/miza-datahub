import logging
from calendar import monthrange
from typing import Optional

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository

logger = logging.getLogger(__name__)


class MizaRealtimeQuery(InfluxRepository):
    """Query for miza_realtime measurement - Machine status data"""

    MACHINE = "Động cơ D31"

    def get_daily_availability(self, date: Optional[str] = None):
        """Get daily average availability for a specific date"""

        start_time_str, end_time_str = TimeUtils().get_production_time_range(
            date
        )

        query = f"""
        SELECT mean("A_1") as "A" FROM (
            SELECT mean("b_status") * 100 as "A_1"
            FROM "miza_realtime"
            WHERE
                ("machine"::tag = '{self.MACHINE}')
                AND time >= '{start_time_str}'
                AND time <= {end_time_str}
            GROUP BY time(1m) fill(null)
        )
        GROUP BY time(1d, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]

    def get_daily_performance(self, date: Optional[str] = None):
        """Get daily average performance for a specific date"""

        start_time_str, end_time_str = TimeUtils().get_production_time_range(
            date
        )

        query = f"""
            SELECT
                "total_ton_B" AS "actual",
                "total_ton_A" AS "target",
                ("total_ton_B" / "total_ton_A") * 100 AS "P"
            FROM (
                SELECT
                    integral("ton_per_min_A", 1m) AS "total_ton_A",
                    integral("ton_per_min_B", 1m) AS "total_ton_B"
                FROM (
                    SELECT
                        "ton_per_min_A",
                        "ton_per_min_B"
                    FROM (
                        SELECT
                        (
                            mean("nominal_speed")
                            * 4.8
                            * mean("nominal_basic_weight")
                            * mean("nominal_efficiency")
                        ) / 100000000 AS "ton_per_min_A"
                        FROM "miza_realtime"
                        WHERE
                            line='Máy giấy PM3'
                            AND machine='Scanner'
                            AND time >= '{start_time_str}'
                            AND time <= {end_time_str}
                        GROUP BY time(1m)
                        fill(none)
                    ), (
                        SELECT
                        (
                            mean("reel_speed")
                            * 4.8
                            * mean("basic_weight")
                            * 0.985
                        ) / 1000000 AS "ton_per_min_B"
                        FROM "miza_realtime"
                        WHERE
                            line='Máy giấy PM3'
                            AND machine='Scanner'
                            AND time >= '{start_time_str}'
                            AND time <= {end_time_str}
                        GROUP BY time(1m)
                        fill(none)
                    )
                )
            )
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]

    def get_last_speed(self):
        query = """
            SELECT
                last("reel_speed") as "reel_speed",
                last("wire_speed") as "wire_speed",
                last("moisture") as "moisture"
            FROM "miza_realtime"
            WHERE
            (
                "line"::tag = 'Máy giấy PM3'
                AND "machine"::tag = 'Scanner'
            )
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0]

    def get_monthly_availability(self, year: int, month: int):
        """Get monthly average availability"""
        last_day = monthrange(year, month)[1]
        query = f"""
        SELECT mean("A") FROM (
            SELECT mean("b_status") * 100 as "A"
            FROM "miza_realtime"
            WHERE
                ("machine"::tag = '{self.MACHINE}')
                AND time >= '{year}-{month:02d}-01T06:00:00+07:00'
                AND time <= '{year}-{month:02d}-{last_day}T06:00:00+07:00' + 1d
            GROUP BY time(1m) fill(null)
        )
        """
        result = self.query(query)
        return self.extract_single_value(result)

    def get_yearly_availability(self, year: int):
        """Get yearly average availability"""
        query = f"""
        SELECT mean("A") FROM (
            SELECT mean("b_status") * 100 as "A"
            FROM "miza_realtime"
            WHERE
                ("machine"::tag = '{self.MACHINE}')
                AND time >= '{year}-01-01T06:00:00+07:00'
                AND time <= '{year+1}-01-01T06:00:00+07:00'
            GROUP BY time(1m) fill(null)
        ) TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return self.extract_single_value(result)

    def get_availability_trend(
        self, start_time: str, end_time: str, interval: str = "1d"
    ):
        query = f"""
        SELECT mean("A")
        FROM (
            SELECT mean("b_status") * 100 AS "A"
            FROM "miza_realtime"
            WHERE
                ("machine"::tag = '{self.MACHINE}')
                AND time >= '{start_time}'
                AND time <= '{end_time}' + 1d
            GROUP BY time(1m)
            fill(null)
        )
        GROUP BY time({interval}, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """

        result = self.query(query)

        return result["results"][0].get("series", [{}])[0].get("values", [])
