import pandas as pd

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class ElectricityWriter(InfluxRepository):
    MEASUREMENT = "electricity_measurement"
    FACTORY_NAME = "Dong Tien Paper Long An"
    MACHINE_NAME = "EVNMeter"

    def write(self, data: list[dict] | pd.DataFrame):
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()

        if df.empty:
            return

        df["dt"] = pd.to_datetime(df["timestamp"], format="%d/%m/%Y")
        df = df.sort_values("dt").reset_index(drop=True)

        tier_cols = ["normal_tier", "peak_tier", "off_peak_tier", "total"]
        for col in tier_cols:
            df[col] = df[col].astype("float")

        df["next_off_peak"] = df["off_peak_tier"].shift(-1)
        df["total_shift"] = (
            df["total"] - df["off_peak_tier"] + df["next_off_peak"]
        )

        factory_esc = self.escape_string(self.FACTORY_NAME)

        lines = []
        for _, row in df.iterrows():
            ts_00 = TimeUtils.date_str_to_vn_timestamp(row["timestamp"])

            ts_06 = TimeUtils.date_str_to_vn_timestamp(row["timestamp"]) + 21600

            metrics_00 = [
                ("Bình Thường", row["normal_tier"]),
                ("Cao Điểm", row["peak_tier"]),
                ("Thấp Điểm", row["off_peak_tier"]),
                ("Tổng Ngày", row["total"]),
            ]

            for name, val in metrics_00:
                name_esc = self.escape_string(name)
                line = (
                    f"{self.MEASUREMENT},"
                    f"factory={factory_esc},"
                    f"machine={self.MACHINE_NAME},"
                    f"name={name_esc} "
                    f"value={val} {ts_00}"
                )
                lines.append(line)

            if pd.notna(row["total_shift"]):
                name_esc = self.escape_string("Tổng Ca 6h")
                line_shift = (
                    f"{self.MEASUREMENT},"
                    f"factory={factory_esc},"
                    f"machine={self.MACHINE_NAME},"
                    f"name={name_esc} "
                    f"value={row['total_shift']} {ts_06}"
                )
                lines.append(line_shift)

        if lines:
            self.client.write("\n".join(lines))
