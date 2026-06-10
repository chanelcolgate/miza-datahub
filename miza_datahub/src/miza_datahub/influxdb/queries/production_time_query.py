from calendar import monthrange

from miza_datahub.influxdb.influx_repository import InfluxRepository


class ProductionTimeQuery(InfluxRepository):
    def get_production_run_time(self, date: str, group_by: str):
        query = f"""
        SELECT sum("cnt")
        FROM (
            SELECT
                last("b_run_2") / 2 AS "cnt"
            FROM "miza_realtime"
            WHERE
                "machine" = 'Động cơ D31'
                AND time >= '{date}T06:00:00+07:00'
                AND time <= '{date}T06:00:00+07:00' + 1d
            GROUP BY time(1m)
            fill(0)
        )
        GROUP BY time({group_by}, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"]

    def get_production_down_time(self, date: str, group_by: str):
        proudct_time = ""
        if group_by == "1d":
            product_time = "1440"
        elif group_by == "1h":
            product_time = "60"

        query = """
        SELECT {product_time} - sum("cnt")
        FROM (
            SELECT
                last("b_run_2") / 2 AS "cnt"
            FROM "miza_realtime"
            WHERE
                "machine" = 'Động cơ D31'
                AND time >= '{date}T06:00:00+07:00'
                AND time <= '{date}T06:00:00+07:00' + 1d
            GROUP BY time(1m)
            fill(0)
        )
        GROUP BY time({group_by}, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """
        result = self.query(query)
        return result["results"][0]["series"]["values"]
