from typing import Iterable
from datetime import datetime, timedelta

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


class ConsumptionWriter(InfluxRepository):
    MEASUREMENT = "consumption_measurement"

    def compute_metrics_for_date_minus_1(self, date: str) -> dict:
        production = PaperDailyOEEQuery(self.client)
        old_date = (
            datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        cut_roll_production = (
            production.get_cut_roll_production(old_date) or 0.0
        )

        air = AirRealtimeQuery(self.client)
        air_used = air.get_daily_air_v2(date) or 0.0

        water = WaterRealtimeQuery(self.client)
        water_used = water.get_daily_water_v2(date) or 0.0
        waste_water_used = water.get_daily_waste_water(date) or 0.0

        return {
            "air_consumption": self._safe_divide(air_used, cut_roll_production),
            "water_consumption": self._safe_divide(
                water_used, cut_roll_production
            ),
            "waste_water_consumption": self._safe_divide(
                waste_water_used, cut_roll_production
            ),
        }

    def compute_metrics_for_date_minus_2(self, date: str) -> dict:
        production = PaperDailyOEEQuery(self.client)
        old_date = (
            datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        cut_roll_production = (
            production.get_cut_roll_production(old_date) or 0.0
        )

        electric = ElectricRealtimeQuery(self.client)
        electric_used = electric.get_daily_electric(date) or 0.0

        return {
            "electric_consumption": self._safe_divide(
                electric_used, cut_roll_production
            )
        }

    def write_for_dates_minus_1(
        self,
        dates: Iterable[str],
        factory: str = "Giấy Đồng Tiến Long An",
        system: str = "OEE",
        machine: str = "PM6",
    ):
        self._write_metrics_for_dates(
            dates,
            self.compute_metrics_for_date_minus_1,
            self.MEASUREMENT,
            factory,
            system,
            machine,
        )

    def write_for_dates_minus_2(
        self,
        dates: Iterable[str],
        factory: str = "Giấy Đồng Tiến Long An",
        system: str = "OEE",
        machine: str = "PM6",
    ):
        self._write_metrics_for_dates(
            dates,
            self.compute_metrics_for_date_minus_2,
            self.MEASUREMENT,
            factory,
            system,
            machine,
        )
