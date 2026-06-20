from calendar import monthrange

from miza_datahub.influxdb.influx_repository import InfluxRepository


class MizaRealtimeQuery(InfluxRepository):
    """Query for miza_realtime measurement - Machine status data"""

    MACHINE = "Động cơ D31"

    def get_daily_availability(self, date: str):
        """Get daily average availability for a specific date"""
        query = f"""
        SELECT mean("A") FROM (
            SELECT mean("b_status") * 100 as "A"
            FROM "miza_realtime"
            WHERE
                ("machine"::tag = '{self.MACHINE}')
                AND time >= '{date}T06:00:00+07:00'
                AND time <= '{date}T06:00:00+07:00' + 1d
            GROUP BY time(1m) fill(null)
        )
        GROUP BY time(1d, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0].get("values", [])

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
        )
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
