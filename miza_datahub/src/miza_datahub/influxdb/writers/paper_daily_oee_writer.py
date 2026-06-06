import pandas as pd

from miza_datahub.influxdb.influx_repository import InfluxRepository


class PaperDailyOEEWriter(InfluxRepository):
    MEASUREMENT = "paper_daily_oee"

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
            timestamp = int(row["production_day"].timestamp())

            tags = [
                f"factory={PaperDailyOEEWriter.escape_string('MIZA Nghi Sơn')}",
                f"line=PM3",
                f"machine=Scanner",
            ]

            values = [
                f"{influx_field}={row[df_field]}"
                for df_field, influx_field in mapping.items()
                if pd.notna(row[df_field])
            ]

            line = f'{self.MEASUREMENT},{",".join(tags)} {",".join(values)} {timestamp}'
            lines.append(line)

        self.client.write("\n".join(lines))
