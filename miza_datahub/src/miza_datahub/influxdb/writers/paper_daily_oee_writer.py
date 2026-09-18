from typing import Iterable
from datetime import datetime, timedelta

import pandas as pd

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository
from miza_datahub.influxdb.queries.oee.paper_daily_oee_query import (
    PaperDailyOEEQuery,
)


class PaperDailyOEEWriter(InfluxRepository):
    MEASUREMENT_OEE = "paper_daily_oee"
    MEASUREMENT_PRODUCTION = "paper_daily_production"

    # def _build_line_protocol(
    #     self,
    #     measurement: str,
    #     tags: List[str],
    #     fields_dict: dict,
    #     timestamp: int,
    # ) -> Optional[str]:
    #     valid_fields = []
    #     for k, v in fields_dict.items():
    #         if v is None or (hasattr(pd, "isna") and pd.isna(v)):
    #             continue
    #         if isinstance(v, str):
    #             safe = v.replace('"', '\\"')
    #             valid_fields.append(f'{k}="{safe}"')
    #         elif isinstance(v, bool):
    #             valid_fields.append(f"{k}={str(v).lower()}")
    #         elif isinstance(v, (int, float)) and not (
    #             isinstance(v, float) and math.isnan(v)
    #         ):
    #             valid_fields.append(f"{k}={v}")

    #     # valid_fields = [
    #     #     f"{k}={v}"
    #     #     for k, v in fields_dict.items()
    #     #     if pd.notna(v) and v is not None
    #     # ]
    #     if not valid_fields:
    #         return None

    #     tag_str = ",".join(tags) if tags else ""
    #     # field_str = ",".join(valid_fields)
    #     # return f"{measurement},{tag_str} {field_str} {timestamp}"
    #     prefix = f"{measurement},{tag_str}" if tag_str else measurement
    #     return f"{prefix} {','.join(valid_fields)} {timestamp}"

    def compute_metrics_for_date(self, date: str) -> dict:
        query = PaperDailyOEEQuery(self.client)
        old_date = (
            datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)
        ).strftime("%Y-%m-%d")

        cut_roll_production = query.get_cut_roll_production(old_date) or 0.0
        roll_production = query.get_roll_production(date) or 0.0
        nominal_production = query.get_nominal_production(date) or 0.0
        availability = query.get_availability(date) or 0.0

        performance = (
            (roll_production / nominal_production * 100.0)
            if nominal_production
            else 0.0
        )
        quality = (
            (min(cut_roll_production / roll_production, 1.0) * 100.0)
            if roll_production
            else 0.0
        )
        oee = (availability * performance * quality) / 10000.0

        run_time_min = 1440.0 * (availability / 100.0)
        down_time_min = 1440.0 - run_time_min

        return {
            "actual": round(cut_roll_production, 2),
            "plan": round(nominal_production, 2),
            "defect": round(max(0.0, roll_production - cut_roll_production), 2),
            "run_time": round(run_time_min, 2),
            "down_time": round(down_time_min, 2),
            "A": round(max(0.0, availability), 2),
            "P": round(max(0.0, performance), 2),
            "Q": round(max(0.0, quality), 2),
            "OEE": round(max(0.0, oee), 2),
        }

    def write_for_dates(
        self,
        dates: Iterable[str],
        factory: str = "Giấy Đồng Tiến Long An",
        system: str = "OEE",
        machine: str = "PM6",
    ):
        self._write_metrics_for_dates(
            dates,
            self.compute_metrics_for_date,
            self.MEASUREMENT_OEE,
            factory,
            system,
            machine,
            hour=7,
        )

    def write_apq(
        self,
        df: pd.DataFrame,
        factory: str = "MIZA Nghi Sơn",
        line: str = "PM3",
        machine: str = "Scanner",
    ):
        lines = []
        mapping = {
            "Sản lượng": "actual",
            "plan": "plan",
            "Hàng lỗi": "defect",
            "run_time": "run_time",
            "ĐG + DM": "down_time",
            "% Hiệu suất": "A",
            "% SL": "P",
            "% Chất lượng": "Q",
            "OEE": "OEE",
        }

        for _, row in df.iterrows():
            ts = row["production_day"]
            timestamp = TimeUtils.to_vn_timestamp(ts)

            tags = [
                f"factory={self.escape_string(factory)}",
                f"line={self.escape_string(line)}",
                f"machine={self.escape_string(machine)}",
            ]

            fields = {
                influx_field: row[df_field]
                for df_field, influx_field in mapping.items()
                if df_field in row and pd.notna(row[df_field])
            }

            one_line = self._build_line_protocol(
                self.MEASUREMENT_OEE, tags, fields, timestamp
            )

            if one_line:
                lines.append(one_line)

        if lines:
            self.client.write("\n".join(lines))

    def write_pq(self, df):
        lines = []
        mapping = {
            "actual": "actual",
            "plan": "plan",
            "B": "defect",
            "P": "P",
            "Q": "Q",
        }

        for _, row in df.iterrows():
            ts = row["production_day"]
            timestamp = TimeUtils.to_vn_timestamp(ts)

            tags = [
                f"factory={PaperDailyOEEWriter.escape_string('MIZA Nghi Sơn')}",
                "line=PM3",
                "machine=Scanner",
            ]

            values = [
                f"{influx_field}={row[df_field]}"
                for df_field, influx_field in mapping.items()
                if pd.notna(row[df_field])
            ]

            line = (
                f'{self.MEASUREMENT},{",".join(tags)} '
                f'{",".join(values)} '
                f"{timestamp}"
            )
            lines.append(line)

        self.client.write("\n".join(lines))
