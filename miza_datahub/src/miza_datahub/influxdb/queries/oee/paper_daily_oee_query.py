from calendar import monthrange

from miza_datahub.influxdb.influx_repository import InfluxRepository


class PaperDailyOEEQuery(InfluxRepository):
    """Query for paper_daily_oee measurement"""

    def get_daily_all_values(self, date: str):
        """Get daily average all values"""
        query = f"""
        SELECT
            mean("A"),
            mean("P"),
            mean("Q"),
            mean("OEE"),
            sum("actual"),
            sum("plan"),
            sum("defect"),
            sum("run_time"),
            sum("down_time")
        FROM "paper_daily_oee"
        WHERE
            time >= '{date}T06:00:00+07:00'
            AND time <= '{date}T06:00:00+07:00' + 1d
        GROUP BY time(1m) fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0].get("values", [])

    def get_monthly_all_values(self, year: int, month: int):
        """Get monthly all values"""
        last_day = monthrange(year, month)[1]
        query = f"""
        SELECT
            mean("A"),
            mean("P"),
            mean("Q"),
            mean("OEE"),
            sum("actual"),
            sum("plan"),
            sum("defect"),
            sum("run_time"),
            sum("down_time")
        FROM "paper_daily_oee"
        WHERE
            time >= '{year}-{month:02d}-01T06:00:00+07:00'
            AND time <= '{year}-{month:02d}-{last_day}T06:00:00+07:00' + 1d
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0].get("values", [])

    def get_yearly_all_values(self, year: int):
        """Get yearly all values"""
        query = f"""
        SELECT
            mean("A"),
            mean("P"),
            mean("Q"),
            mean("OEE"),
            sum("actual"),
            sum("plan"),
            sum("defect"),
            sum("run_time"),
            sum("down_time")
        FROM "paper_daily_oee"
        WHERE
            time >= '{year}-01-01T06:00:00+07:00'
            AND time <= '{year+1}-01-01T06:00:00+07:00'
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0].get("series", [{}])[0].get("values", [])

    def get_all_values_trend(
        self, start_time: str, end_time: str, interval: str = "1d"
    ):
        query = f"""
        SELECT
            mean("A"),
            mean("P"),
            mean("Q"),
            mean("OEE"),
            sum("actual"),
            sum("plan"),
            sum("defect"),
            sum("run_time"),
            sum("down_time")
        FROM "paper_daily_oee"
        WHERE
            time >= '{start_time}'
            AND time <= '{end_time}' + 1d
        GROUP BY time({interval}, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """

        result = self.query(query)

        return result["results"][0].get("series", [{}])[0].get("values", [])

    def delete_all_values_error(self):
        results = self.query("""
            SELECT * FROM "paper_daily_oee"
            WHERE
                time >= 1780854202295ms
                AND time <= 1782389990487ms
        """)

        series = results["results"][0].get("series", [])
        ts = []

        for point in series[0]["values"]:
            timestamp = point[0]

            if timestamp.endswith("T00:00:00Z"):
                self.query(f"""
                    DELETE FROM "paper_daily_oee"
                    WHERE
                    time = '{timestamp}'
                """)
        return ts
