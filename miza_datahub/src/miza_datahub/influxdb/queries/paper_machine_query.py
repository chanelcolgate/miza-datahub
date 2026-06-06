from miza_datahub.influxdb.influx_repository import InfluxRepository


class PaperMachineRepository(InfluxRepository):
    def get_actual_production(self, start_time: str, end_time: str) -> float:
        query = f"""
        SELECT integral("ton_per_min",1m)
        FROM (
            SELECT
            (
                mean("reel_speed")
                * 4.8
                * mean("basic_weight")
                * 0.9
            ) / 1000000 AS ton_per_min
            FROM miza_realtime
            WHERE
                line='Máy giấy PM3'
                AND machine='Scanner'
                AND time >= '{start_time}'
                AND time <= '{end_time}'
            GROUP BY time(1m)
        )
        """

        result = self.query(query)
        print(result)
        return result["results"][0]["series"][0]["values"][0][1]

    def get_plan_production(self, start_time: str, end_time: str) -> float:
        query = f"""
        SELECT integral("ton_per_min",1m)
        FROM (
            SELECT
            (
                mean("nominal_speed")
                * 4.8
                * mean("nominal_basic_weight")
                * mean("nominal_efficiency")
            ) / 100000000 AS ton_per_min
            FROM miza_realtime
            WHERE
                line='Máy giấy PM3'
                AND machine='Scanner'
                AND time >= '{start_time}'
                AND time <= '{end_time}'
            GROUP BY time(1m)
        )
        """
        result = self.query(query)
        return result["results"][0]["series"][0]["values"][0][1]

    def get_actual_production_daily(self, start_time: str, end_time: str):
        query = f"""
        SELECT integral("ton_per_min",1m)
        FROM (
            SELECT
            (
                mean("reel_speed")
                * 4.8
                * mean("basic_weight")
                * 0.9
            ) / 1000000 AS ton_per_min
            FROM miza_realtime
            WHERE
                line='Máy giấy PM3'
                AND machine='Scanner'
                AND time >= '{start_time}'
                AND time <= '{end_time}'
            GROUP BY time(1m)
        )
        GROUP BY time(1d, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """

        result = self.query(query)
        return result["results"][0]["series"][0]["values"]

    def get_plan_production_daily(self, start_time: str, end_time: str):
        query = f"""
        SELECT integral("ton_per_min",1m)
        FROM (
            SELECT
            (
                mean("nominal_speed")
                * 4.8
                * mean("nominal_basic_weight")
                * mean("nominal_efficiency")
            ) / 100000000 AS ton_per_min
            FROM miza_realtime
            WHERE
                line='Máy giấy PM3'
                AND machine='Scanner'
                AND time >= '{start_time}'
                AND time <= '{end_time}'
            GROUP BY time(1m)
        )
        GROUP BY time(1d, 6h)
        fill(none)
        TZ('Asia/Ho_Chi_Minh')
        """

        result = self.query(query)
        return result["results"][0]["series"][0]["values"]
