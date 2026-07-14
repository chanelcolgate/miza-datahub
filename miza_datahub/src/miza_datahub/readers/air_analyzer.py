import logging
from io import BytesIO

import pandas as pd
import numpy as np

from miza_datahub.readers.base_reader import BaseReader
from miza_datahub.influxdb.writers.air_analyzer import AirAnalyzerWriter

logger = logging.getLogger(__name__)


class AirAnalyzer(BaseReader):
    def load(self):
        try:
            df = pd.read_excel(
                BytesIO(self.file_bytes), sheet_name="Báo cáo hơi", header=None
            )
        except Exception as e:
            logger.error(f"Failed to load workbook from BytesIO: {e}")
            raise

        time_markers = df.iloc[0, 2:].tolist()

        timeline = []
        base_day_str = str(df.iloc[0, 1]).strip()
        current_date = pd.to_datetime(base_day_str, dayfirst=True)

        previous_hour = -1

        for marker in time_markers:
            if isinstance(marker, pd.Timestamp) or hasattr(marker, "strftime"):
                current_date = pd.to_datetime(
                    str(marker).strip(), format="%Y-%m-%d %H:%M:%S"
                )
                previous_hour = -1
                continue

            try:
                current_hour = int(marker)
            except Exception:
                logger.error(marker)

            if current_hour == 24:
                current_hour = 0
                current_date = current_date + pd.Timedelta(days=1)
                previous_hour = 0
            else:
                if previous_hour != -1 and current_hour < previous_hour:
                    current_date = current_date + pd.Timedelta(days=1)
                previous_hour = current_hour

            time_str = f"{current_hour:02d}:00:00"

            full_timestamp = current_date.normalize() + pd.to_timedelta(
                time_str
            )

            timeline.append(full_timestamp)

        df_matrix = df.iloc[1:38, 1:]

        df_matrix = df_matrix.replace(
            {
                "#DIV/0!": 0,
                "#ERROR!": np.nan,
                "#VALUE!": np.nan,
                "#REF!": np.nan,
                "#NAME?": np.nan,
            }
        )

        row_1_data = df_matrix.iloc[1]
        clean_columns_condition = row_1_data.notna()

        df_clean = df_matrix.loc[:, clean_columns_condition]

        df_final = df_clean.T
        df_final.index = timeline[: len(df_final.index)]
        df_final.columns = [
            "Áp tổng lò",
            "Chỉ số đồng hồ hơi 1",
            "Chỉ số đồng hồ hơi 2",
            "Nhiệt độ đường hơi 1",
            "Nhiệt độ đường hơi 2",
            "Đường hơi (1)",
            "Đường hơi (2)",
            "Trưởng ca xeo",
            "Loại giấy chạy",
            "Tốc độ trung bình trong giờ",
            "Tốc độ định mức",
            "Chênh lệch tốc độ",
            "ĐL giấy",
            "Tổng hơi (Tấn)",
            "Sản lượng (Tấn)",
            "Bột dùng (Tấn)",
            "Tiêu hao thực tế",
            "Tiêu hao định mức",
            "% Tiêu hao TT/ĐM",
            "Nhiệt độ PTN",
            "Độ ẩm (%)",
            "Chênh áp lô sấy số 1",
            "Chênh áp lô sấy 2-6",
            "Chênh áp lô sấy 7-17",
            "Chênh áp lô sấy 18-29",
            "Chênh áp lô sấy 30",
            "Chênh áp lô sấy 31",
            "Chênh áp lô sấy 32-43",
            "Chênh áp lô sấy 36-42",
            "Áp lực ép 1",
            "Áp lực ép 2",
            "Áp lực ép 3",
            "Lực ép keo",
            "Tình trạng chăn đã sử dụng",
            "Đứt giấy-dừng (phút)",
            "Lực ép quang",
            "Ghi chú",
        ]
        df_final["Áp tổng lò"] = df_final["Áp tổng lò"].astype(np.float16)
        df_final["Chỉ số đồng hồ hơi 1"] = (
            df_final["Chỉ số đồng hồ hơi 1"].fillna(0).astype(np.uint32)
        )
        df_final["Chỉ số đồng hồ hơi 2"] = (
            df_final["Chỉ số đồng hồ hơi 2"].fillna(0).astype(np.uint32)
        )
        df_final["Nhiệt độ đường hơi 1"] = (
            df_final["Nhiệt độ đường hơi 1"].fillna(0).astype(np.uint8)
        )
        df_final["Nhiệt độ đường hơi 2"] = (
            df_final["Nhiệt độ đường hơi 2"].fillna(0).astype(np.uint8)
        )
        df_final["Đường hơi (1)"] = (
            df_final["Đường hơi (1)"].fillna(0).astype(np.uint8)
        )
        df_final["Đường hơi (2)"] = (
            df_final["Đường hơi (2)"].fillna(0).astype(np.uint8)
        )
        df_final["Tốc độ trung bình trong giờ"] = (
            df_final["Tốc độ trung bình trong giờ"].fillna(0).astype(np.uint16)
        )
        df_final["Tốc độ định mức"] = (
            df_final["Tốc độ định mức"].fillna(0).astype(np.uint16)
        )
        df_final["Chênh lệch tốc độ"] = (
            df_final["Chênh lệch tốc độ"].fillna(0).astype(np.int16)
        )
        df_final["ĐL giấy"] = df_final["ĐL giấy"].fillna(0).astype(np.uint16)
        df_final["Tổng hơi (Tấn)"] = (
            df_final["Tổng hơi (Tấn)"].fillna(0).astype(np.uint8)
        )
        df_final["Sản lượng (Tấn)"] = (
            df_final["Sản lượng (Tấn)"].fillna(0).astype(np.float16)
        )
        df_final["Bột dùng (Tấn)"] = (
            df_final["Bột dùng (Tấn)"].fillna(0).astype(np.float16)
        )
        df_final["Tiêu hao thực tế"] = (
            df_final["Tiêu hao thực tế"].fillna(0).astype(np.float32)
        )
        df_final["Tiêu hao định mức"] = (
            df_final["Tiêu hao định mức"].fillna(0).astype(np.float32)
        )
        df_final["% Tiêu hao TT/ĐM"] = (
            df_final["% Tiêu hao TT/ĐM"].fillna(0).astype(np.float32)
        )
        df_final["Nhiệt độ PTN"] = (
            df_final["Nhiệt độ PTN"].fillna(0).astype(np.uint8)
        )
        df_final["Độ ẩm (%)"] = (
            df_final["Độ ẩm (%)"].fillna(0).astype(np.float16)
        )
        df_final["Chênh áp lô sấy số 1"] = (
            df_final["Chênh áp lô sấy số 1"].fillna(0).astype(np.uint8)
        )
        df_final["Chênh áp lô sấy 2-6"] = (
            df_final["Chênh áp lô sấy 2-6"].fillna(0).astype(np.uint8)
        )
        df_final["Chênh áp lô sấy 7-17"] = (
            df_final["Chênh áp lô sấy 7-17"].fillna(0).astype(np.uint8)
        )
        df_final["Chênh áp lô sấy 18-29"] = (
            df_final["Chênh áp lô sấy 18-29"].fillna(0).astype(np.uint8)
        )
        df_final["Chênh áp lô sấy 30"] = (
            df_final["Chênh áp lô sấy 30"].fillna(0).astype(np.uint8)
        )
        df_final["Chênh áp lô sấy 31"] = (
            df_final["Chênh áp lô sấy 31"].fillna(0).astype(np.uint8)
        )
        df_final["Chênh áp lô sấy 32-43"] = (
            df_final["Chênh áp lô sấy 32-43"].fillna(0).astype(np.uint8)
        )
        df_final["Chênh áp lô sấy 36-42"] = (
            df_final["Chênh áp lô sấy 36-42"].fillna(0).astype(np.uint8)
        )
        df_final["Đứt giấy-dừng (phút)"] = (
            df_final["Đứt giấy-dừng (phút)"].fillna(0).astype(np.uint16)
        )
        self.df = (
            df_final[
                [
                    "Chỉ số đồng hồ hơi 1",
                    "Chỉ số đồng hồ hơi 2",
                    "Nhiệt độ đường hơi 1",
                    "Nhiệt độ đường hơi 2",
                    "Loại giấy chạy",
                ]
            ]
            .reset_index()
            .rename(columns={"index": "production_day"})
        )

    def write(self):
        self.load()
        air_analyzer_writer = AirAnalyzerWriter(self.influx)
        air_analyzer_writer.write(self.df)
        return True
