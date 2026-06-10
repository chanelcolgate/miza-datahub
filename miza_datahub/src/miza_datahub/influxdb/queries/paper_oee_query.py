from calendar import monthrange

from miza_datahub.influxdb.influx_repository import InfluxRepository


class PaperOEEQuery(InfluxRepository):
    def get_daily_availability(self, date: str):
        query = f"""
        SELECT mean("A") FROM (
          SELECT mean("b_status") * 100 as "A"
          FROM "miza_realtime"
          WHERE
            ("machine"::tag = 'Động cơ D31')
            AND time >= '{date}T06:00:00+07:00'
            AND time <= '{date}T06:00:00+07:00' + 1d
          GROUP BY time(1m) fill(null)
        )
        GROUP BY time(1d, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"]

    def get_daily_performance_quality(self, date: str):
        query = f"""
        SELECT mean("P"), mean("Q")
        FROM "paper_daily_oee"
        WHERE
            time >= '{date}T06:00:00+07:00'
            AND time <= '{date}T06:00:00+07:00' + 1d
        GROUP BY time(1m) fill(none)
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"]

    def get_monthly_availability(self, year: int, month: int):
        last_day = monthrange(year, month)[1]
        query = f"""
        SELECT mean("A") FROM (
          SELECT mean("b_status") * 100 as "A"
          FROM "miza_realtime"
          WHERE
            ("machine"::tag = 'Động cơ D31')
            AND time >= '{year}-{month:02d}-01T06:00:00+07:00'
            AND time <= '{year}-{month:02d}-{last_day}T06:00:00+07:00' + 1d
          GROUP BY time(1m) fill(null)
        )
        GROUP BY time(4w, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"]

    def get_monthly_performance_quality(self, year: int, month: int):
        last_day = monthrange(year, month)[1]
        query = f"""
        SELECT mean("P"), mean("Q")
        FROM "paper_daily_oee"
        WHERE
            time >= '{year}-{month:02d}-01T06:00:00+07:00'
            AND time <= '{year}-{month:02d}-{last_day}T06:00:00+07:00' + 1d
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"]

    def get_yearly_availability(self, year: int):
        query = f"""
        SELECT mean("A") FROM (
          SELECT mean("b_status") * 100 as "A"
          FROM "miza_realtime"
          WHERE
            ("machine"::tag = 'Động cơ D31')
            AND time >= '{year}-01-01T06:00:00+07:00'
            AND time <= '{year+1}-01-01T06:00:00+07:00'
          GROUP BY time(1m) fill(null)
        )
        GROUP BY time(52w, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"]

    def get_yearly_performance_quality(self, year: int):
        query = f"""
        SELECT mean("P"), mean("Q")
        FROM "paper_daily_oee"
        WHERE
            time >= '{year}-01-01T06:00:00+07:00'
            AND time <= '{year+1}-01-01T06:00:00+07:00'
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"]
