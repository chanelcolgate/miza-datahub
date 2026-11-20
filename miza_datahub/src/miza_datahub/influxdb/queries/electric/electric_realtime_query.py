from miza_datahub.services import shift_calendar
from miza_datahub.influxdb.influx_repository import InfluxRepository


class ElectricRealtimeQuery(InfluxRepository):
    def get_daily_electric(self, date: str):
        start, end = shift_calendar.production_day_range(date)
        query = f"""
            SELECT
                mean("value") AS "electric_used"
            FROM "electricity_measurement"
            WHERE
                "name" =~ /^Tổng Ca (6|7)h$/
                AND time >= '{start.isoformat()}'
                AND time < '{end.isoformat()}'
            GROUP BY time(1h) fill(none)
        """
        result = self.query(query)
        return (
            result["results"][0].get("series", [{}])[0].get("values", [])[0][1]
        )
