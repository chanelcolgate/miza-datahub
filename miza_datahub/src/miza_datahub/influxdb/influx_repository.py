import math
from typing import List, Optional, Iterable

import pandas as pd

from miza_datahub.services.time_utils import TimeUtils


class InfluxRepository:
    def __init__(self, client):
        self.client = client

    def query(self, sql):
        return self.client.query(sql)

    def write(self, line_protocol):
        return self.client.write(line_protocol)

    def _safe_divide(self, numerator: float, denominator: float) -> float:
        if not denominator or denominator <= 0:
            return 0.0
        return round(numerator / denominator, 2)

    def _build_line_protocol(
        self,
        measurement: str,
        tags: List[str],
        fields_dict: dict,
        timestamp: int,
    ) -> Optional[str]:
        valid_fields = []
        for k, v in fields_dict.items():
            if v is None or (hasattr(pd, "isna") and pd.isna(v)):
                continue
            if isinstance(v, str):
                safe = v.replace('"', '\\"')
                valid_fields.append(f'{k}="{safe}"')
            elif isinstance(v, bool):
                valid_fields.append(f"{k}={str(v).lower()}")
            elif isinstance(v, (int, float)) and not (
                isinstance(v, float) and math.isnan(v)
            ):
                valid_fields.append(f"{k}={v}")

        if not valid_fields:
            return None

        tag_str = ",".join(tags) if tags else ""
        prefix = f"{measurement},{tag_str}" if tag_str else measurement
        return f"{prefix} {','.join(valid_fields)} {timestamp}"

    def _write_metrics_for_dates(
        self,
        dates: Iterable[str],
        compute_fn,
        measurement: str,
        factory: str,
        system: str,
        machine: str,
    ) -> None:
        lines = []
        tags = [
            f"factory={self.escape_string(factory)}",
            f"system={self.escape_string(system)}",
            f"machine={self.escape_string(machine)}",
        ]

        for date in dates:
            metrics = compute_fn(date)
            if not metrics or all(v == 0.0 for v in metrics.values()):
                continue

            timestamp = TimeUtils.date_str_to_vn_timestamp(date, fmt="%Y-%m-%d")
            consumption_line = self._build_line_protocol(
                measurement, tags, metrics, timestamp
            )
            if consumption_line:
                lines.append(consumption_line)

        if lines:
            self.client.write("\n".join(lines))

    @staticmethod
    def escape_string(string):
        return string.translate(
            string.maketrans({",": r"\,", " ": r"\ ", "=": r"\="})
        )

    @staticmethod
    def extract_single_value(result):
        series = result["results"][0].get("series", [])

        if not series:
            return None

        values = series[0].get("values", [])

        if not values:
            return None

        return values[0][1]
