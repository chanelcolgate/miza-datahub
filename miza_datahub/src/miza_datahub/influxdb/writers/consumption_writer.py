from typing import Iterable

from miza_datahub.influxdb.influx_repository import InfluxRepository
from miza_datahub.influxdb.queries.oee.paper_daily_oee_query import (
    PaperDailyOEEQuery,
)
from miza_datahub.influxdb.queries.air.air_realtime_query import (
    AirRealtimeQuery,
)
from miza_datahub.influxdb.queries.water.water_realtime_query import (
    WaterRealtimeQuery,
)
from miza_datahub.influxdb.queries.electric.electric_realtime_query import (
    ElectricRealtimeQuery,
)
from miza_datahub.services.time_utils import TimeUtils


class ConsumptionWriter(InfluxRepository):
    MEASUREMENT = "consumption_measurement"

    def compute_metrics_for_date_minus_1(self, date: str) -> dict:
        production = PaperDailyOEEQuery(self.client)
        cut_roll_production = production.get_cut_roll_production(date) or 0.0

        air = AirRealtimeQuery(self.client)
        air_used = air.get_daily_air_v2(date) or 0.0

        water = WaterRealtimeQuery(self.client)
        water_used = water.get_daily_water_v2(date) or 0.0
        waste_water_used = water.get_daily_waste_water(date) or 0.0

        air_consumption = (cut_roll_production / air_used) if air_used else 0.0

        water_consumption = (
            (cut_roll_production / water_used) if water_used else 0.0
        )

        waste_water_consumption = (
            (cut_roll_production / waste_water_used)
            if waste_water_used
            else 0.0
        )

        return {
            "air_consumption": round(air_consumption, 2),
            "water_consumption": round(water_consumption, 2),
            "waste_water_consumption": round(waste_water_consumption, 2),
        }

    def compute_metrics_for_date_minus_2(self, date: str) -> dict:
        production = PaperDailyOEEQuery(self.client)
        cut_roll_production = production.get_cut_roll_production(date) or 0.0

        electric = ElectricRealtimeQuery(self.client)
        electric_used = electric.get_daily_electric(date) or 0.0

        electric_consumption = (
            (cut_roll_production / electric_used) if electric_used else 0.0
        )

        return {"electric_consumption": round(electric_consumption, 2)}

    def write_for_dates_minus_1(
        self,
        dates: Iterable[str],
        factory: str = "Giấy Đồng Tiến Long An",
        system: str = "OEE",
        machine: str = "PM6",
    ):
        lines = []
        for date in dates:
            metrics = self.compute_metrics_for_date_minus_1(date)
            timestamp = TimeUtils.date_str_to_vn_timestamp(date, fmt="%Y-%m-%d")

            tags = [
                f"factory={self.escape_string(factory)}",
                f"system={self.escape_string(system)}",
                f"machine={self.escape_string(machine)}",
            ]
            consumption_line = self._build_line_protocol(
                self.MEASUREMENT, tags, metrics, timestamp
            )
            if consumption_line:
                lines.append(consumption_line)

        if lines:
            self.client.write("\n".join(lines))
