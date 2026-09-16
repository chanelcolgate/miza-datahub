from miza_datahub.influxdb.influx_repository import InfluxRepository


class ElectricRealtimeQuery(InfluxRepository):
    def get_daily_electric(self, date: str):
        query = f"""
        SELECT
            SUM("electric_used") AS "sum_electric"
        FROM
        (
            SELECT
                mean("value") AS "electric_used"
            FROM "electricity_measurement"
            WHERE
                "name" = 'Tổng Ca 6h'
                AND time >= '{date}T07:00:00+07:00'
                AND time <= '{date}T07:00:00+07:00' + 1d
            GROUP BY time(1d) fill(none)
        )
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )
