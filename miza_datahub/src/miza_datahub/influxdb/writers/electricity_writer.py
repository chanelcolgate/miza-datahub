import pandas as pd

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class ElectricityWriter(InfluxRepository):
    MEASUREMENT = "electricity_measurement"

    def write(self, data: list[dict] | pd.DataFrame):
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data

        if df.empty:
            return

        lines = []
        for _, row in df.iterrows():
            ts_str = row["timestamp"]

            # Timestamp
            timestamp = TimeUtils.date_str_to_vn_timestamp(ts_str)

            factory_esc = ElectricityWriter.escape_string(
                "Dong Tien Paper Long An"
            )

            # Tags
            normal_tags = [
                f"factory={factory_esc}",
                "machine=EVNMeter",
                f"name={ElectricityWriter.escape_string('Bình Thường')}",
            ]

            peak_tags = [
                f"factory={factory_esc}",
                "machine=EVNMeter",
                f"name={ElectricityWriter.escape_string('Cao Điểm')}",
            ]

            off_peak_tags = [
                f"factory={factory_esc}",
                "machine=EVNMeter",
                f"name={ElectricityWriter.escape_string('Thấp Điểm')}",
            ]

            # Values
            normal_values = f"value={float(row['normal_tier'])}"
            peak_values = f"value={float(row['peak_tier'])}"
            off_peak_values = f"value={float(row['off_peak_tier'])}"

            # Line
            normal_line = (
                f"{self.MEASUREMENT},{','.join(normal_tags)} "
                f"{normal_values }"
                f"{timestamp}"
            )

            peak_line = (
                f"{self.MEASUREMENT},{','.join(peak_tags)} "
                f"{peak_values }"
                f"{timestamp}"
            )

            off_peak_line = (
                f"{self.MEASUREMENT},{','.join(off_peak_tags)} "
                f"{off_peak_values }"
                f"{timestamp}"
            )

            lines.append(normal_line)
            lines.append(peak_line)
            lines.append(off_peak_line)

        print(lines)
        self.client.write("\n".join(lines))
