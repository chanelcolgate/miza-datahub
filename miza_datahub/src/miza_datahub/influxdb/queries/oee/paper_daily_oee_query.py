from calendar import monthrange
from datetime import datetime, timedelta

from miza_datahub.influxdb.influx_repository import InfluxRepository


class PaperDailyOEEQuery(InfluxRepository):
    """Query for paper_daily_oee measurement"""

    def create_paper_daily_oee(self, date: str):
        old_date = (
            datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        cut_roll_production = self.get_cut_roll_production(old_date)
        roll_production = self.get_roll_production(date)
        nominal_production = self.get_nominal_production(date)
        availability = self.get_availability(date)

        performance = (roll_production / nominal_production) * 100
        quality = min(cut_roll_production / roll_production, 1.0) * 100
        oee = availability * performance * quality / 10000

        run_time_min = 1440 * availability / 100
        downtime_min = 1440 - run_time_min
        return oee, run_time_min, downtime_min

    def get_cut_roll_production(self, date: str):
        query = f"""
        SELECT
            sum("weight") / 1000
        FROM "cut_roll_production"
        WHERE
            time >= '{date}T07:00:00+07:00'
            AND time <= '{date}T07:00:00+07:00' + 1d
        GROUP BY time(1d,-7h) fill(none)
        ORDER BY time ASC
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )

    def get_roll_production(self, date: str):
        query = f"""
        SELECT SUM("hourly_production") AS "production"
        FROM (
            SELECT integral("ton_per_min", 1m) AS "hourly_production"
            FROM (
                SELECT
                    (
                        mean("speed_machine") *
                        4.6 *
                        mean("basic_weight") *
                        0.97
                    ) / 1000000 AS "ton_per_min"
                FROM "dongtien_realtime"
                WHERE
                    "machine" = 'PM6'
                    AND time >= '{date}T07:00:00+07:00'
                    and time <= '{date}T07:00:00+07:00' + 1d
                GROUP BY time(1m)
                fill(0)
            )
            GROUP BY time(1h)
            fill(0)
        )
        WHERE
            time >= '{date}T07:00:00+07:00'
            and time <= '{date}T07:00:00+07:00'+ 1d
        GROUP BY time(1d)
        fill(none)
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )

    def get_nominal_production(self, date: str):
        query = f"""
        SELECT SUM("hourly_production") AS "nominal_production"
        FROM (
            SELECT integral("ton_per_min", 1m) AS "hourly_production"
            FROM (
                SELECT
                    (
                        mean("nominal_speed") *
                        4.6 *
                        mean("nominal_bw")
                    ) / 1000000 AS "ton_per_min"
                FROM "paper_daily_nominal"
                WHERE
                    "machine" = 'PM6'
                    AND time >= '{date}T07:00:00+07:00'
                    and time <= '{date}T07:00:00+07:00' + 1d
                GROUP BY time(1m)
                fill(none)
            )
            GROUP BY time(1h)
            fill(0)
        )
        WHERE
            time >= '{date}T07:00:00+07:00'
            and time <= '{date}T07:00:00+07:00' + 1d
        GROUP BY time(1d)
        fill(none)
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )

    def get_availability(self, date):
        query = f"""
        SELECT mean("hourly_A") AS "Availability"
        FROM (
            SELECT
                mean("A") AS "hourly_A"
            FROM (
                SELECT
                    mean("b_status") * 100 AS "A"
                FROM "dongtien_realtime"
                WHERE
                    "machine" = 'PM6'
                    AND time >= '{date}T07:00:00+07:00'
                    and time <= '{date}T07:00:00+07:00' + 1d
                GROUP BY time(1m)
                fill(none)
            )
            GROUP BY time(1h)
            fill(none)
        )
        WHERE
            time >= '{date}T07:00:00+07:00'
            and time <= '{date}T07:00:00+07:00' + 1d
        GROUP BY time(1d)
        fill(none)
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )

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
