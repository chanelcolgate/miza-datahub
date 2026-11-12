import logging

from miza_datahub.services.time_utils import TimeUtils
from miza_datahub.influxdb.influx_repository import InfluxRepository

logger = logging.getLogger(__name__)


class JumboRollWriter(InfluxRepository):
    MEASUREMENT = "jumbo_roll_production"

    def write(self, df):
        lines = []
        for _, row in df.iterrows():
            ts = row["jumbo_prod_time"]
            try:
                timestamp = TimeUtils.to_vn_timestamp(ts)
            except ValueError:
                logger.info(row)

            tags = [
                f"factory={self.escape_string('Giấy Đồng Tiến Long An')}",
                f"shift={self.escape_string(str(row['jumbo_shift']))}",
                f"crew={self.escape_string(str(row['jumbo_crew']))}",
                f"jumbo_id={self.escape_string(str(row['Mã cuộn']))}",
            ]

            values = ["jumbo_roll_qty=1", f"weight={float(row['Khối lượng'])}"]

            line = (
                f"{self.MEASUREMENT},{','.join(tags)} "
                f"{','.join(values)} "
                f"{timestamp}"
            )
            lines.append(line)

        if lines:
            try:
                self.client.write("\n".join(lines))
            except Exception as e:
                print(e)


class CutRollWriter(InfluxRepository):
    MEASUREMENT = "cut_roll_production"

    def write(self, df):
        lines = []
        for _, row in df.iterrows():
            ts = row["Ngày cắt cuộn con"]
            timestamp = TimeUtils.to_vn_timestamp(ts)

            tags = [
                f"factory={self.escape_string('Giấy Đồng Tiến Long An')}",
                f"paper_type={self.escape_string(str(row['Loại giấy']))}",
                f"customer={self.escape_string(str(row['Khách hàng']))}",
                f"crew={self.escape_string(str(row['Ca cắt']))}",
                f"jumbo_id={self.escape_string(str(row['Mã cuộn']))}",
            ]

            values = [
                "cut_roll_qty=1",
                f"weight={float(row['Khối lượng'])}",
                f"basic_weight={float(row['Định lượng trung bình'])}",
                f"burse_strength={float(row['Bục trung bình'])}",
                f"ring_crush={float(row['Nén vòng trung bình'])}",
            ]

            line = (
                f"{self.MEASUREMENT},{','.join(tags)} "
                f"{','.join(values)} "
                f"{timestamp}"
            )
            lines.append(line)

        if lines:
            try:
                self.client.write("\n".join(lines))
            except Exception as e:
                print(e)
