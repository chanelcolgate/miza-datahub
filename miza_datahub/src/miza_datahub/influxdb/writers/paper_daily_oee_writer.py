import pandas as pd

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class PaperDailyOEEWriter(InfluxRepository):
    MEASUREMENT_OEE = "paper_daily_oee"
    MEASUREMENT_PRODUCTION = "paper_daily_production"

    def _build_line_protocol(
        self,
        measurement: str,
        tags: list[str],
        fields_dict: dict,
        timestamp: int,
    ) -> str | None:
        """Helper dựng Influx Line Protocol string từ tags và dict fields."""
        valid_fields = [
            f"{k}={v}"
            for k, v in fields_dict.items()
            if pd.notna(v) and v is not None
        ]
        if not valid_fields:
            return None

        tag_str = ",".join(tags)
        field_str = ",".join(valid_fields)
        return f"{measurement},{tag_str} {field_str} {timestamp}"

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

            values = [
                f"{influx_field}={row[df_field]}"
                for df_field, influx_field in mapping.items()
                if pd.notna(row[df_field])
            ]

            line = self._build_line_protocol(
                self.MEASUREMENT_OEE, tags, fields, timestamp
            )

            if line:
                lines.append(line)

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

    def write_apq_v2(
        self,
        df: pd.DataFrame,
        factory: str = "Giấy Đồng Tiến Long An",
        system: str = "OEE",
        machine: str = "PM6",
        paper_type: str = "M6S",
    ):
        pass
