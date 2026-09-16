import math
from typing import List, Optional

import pandas as pd


class InfluxRepository:
    def __init__(self, client):
        self.client = client

    def query(self, sql):
        return self.client.query(sql)

    def write(self, line_protocol):
        return self.client.write(line_protocol)

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
