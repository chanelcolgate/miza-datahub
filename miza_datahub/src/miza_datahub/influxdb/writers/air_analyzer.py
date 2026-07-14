from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository


class AirAnalyzerWriter(InfluxRepository):
    MEASUREMENT = "air_measurement"

    def write(self, df):
        lines = []
        for _, row in df.iterrows():
            ts = row["production_day"]
            timestamp = TimeUtils.to_vn_timestamp(ts)

            # Duong hoi 1

            tags_1 = [
                f"factory={AirAnalyzerWriter.escape_string('MIZA Nghi Sơn')}",
                "line=PM3",
                "machine=Air",
                f"paper_grade={row['Loại giấy chạy']}",
                f"name={AirAnalyzerWriter.escape_string('Đường hơi 1')}",
            ]

            values_1 = [
                f"meter={float(row['Chỉ số đồng hồ hơi 1'])}",
            ]

            line_1 = (
                f"{self.MEASUREMENT},{','.join(tags_1)} "
                f"{','.join(values_1)} "
                f"{timestamp}"
            )
            lines.append(line_1)

            # Duong hoi 2

            tags_2 = [
                f"factory={AirAnalyzerWriter.escape_string('MIZA Nghi Sơn')}",
                "line=PM3",
                "machine=Air",
                f"paper_grade={row['Loại giấy chạy']}",
                f"name={AirAnalyzerWriter.escape_string('Đường hơi 2')}",
            ]

            values_2 = [
                f"meter={float(row['Chỉ số đồng hồ hơi 2'])}",
            ]

            line_2 = (
                f"{self.MEASUREMENT},{','.join(tags_2)} "
                f"{','.join(values_2)} "
                f"{timestamp}"
            )
            lines.append(line_2)

        self.client.write("\n".join(lines))
