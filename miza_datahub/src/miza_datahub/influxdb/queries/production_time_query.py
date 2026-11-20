from miza_datahub.services import shift_calendar
from miza_datahub.influxdb.influx_repository import InfluxRepository


class ProductionTimeQuery(InfluxRepository):
    def get_production_run_time(self, date: str, group_by: str):
        start, end = shift_calendar.production_day_range(date)
        query = f"""
        SELECT sum("cnt")
        FROM (
            SELECT
                last("b_run_2") / 2 AS "cnt"
            FROM "miza_realtime"
            WHERE
                "machine" = 'Động cơ D31'
                AND time >= '{start.isoformat()}'
                AND time < '{end.isoformat()}'
            GROUP BY time(1m)
            fill(0)
        )
        GROUP BY time({group_by}, 7h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"]

    def get_production_down_time(self, date: str, group_by: str):
        start, end = shift_calendar.production_day_range(date)
        product_time = ""
        if group_by == "1d":
            product_time = "1440"
        elif group_by == "1h":
            product_time = "60"

        query = f"""
        SELECT {product_time} - sum("cnt")
        FROM (
            SELECT
                last("b_run_2") / 2 AS "cnt"
            FROM "miza_realtime"
            WHERE
                "machine" = 'Động cơ D31'
                AND time >= '{start.isoformat()}'
                AND time < '{end.isoformat()}'
            GROUP BY time(1m)
            fill(0)
        )
        GROUP BY time({group_by}, 7h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"]["values"]
