from io import BytesIO

import numpy as np
import pandas as pd

from miza_datahub.readers.base_reader import BaseReader
from miza_datahub.influxdb.writers.paper_daily_oee_writer import (
    PaperDailyOEEWriter,
)


class OEEAnalyzer(BaseReader):
    def load(self):
        excel_file = pd.ExcelFile(BytesIO(self.file_bytes))
        df_raw = pd.read_excel(
            BytesIO(self.file_bytes), sheet_name="OEE", header=None
        )

        sheet_name = excel_file.sheet_names[0]
        month_str, year_str = sheet_name.split(".")
        month = int(month_str)
        year = 2000 + int(year_str)

        time_markers = df_raw.iloc[0, 2:].tolist()

        timeline = []
        for marker in time_markers:
            current_day = int(marker)
            full_timestamp = pd.to_datetime(
                f"{current_day}/{month}/{year} 06:00", dayfirst=True
            )
            timeline.append(full_timestamp)

        df_matrix = df_raw.iloc[1:10, 2:]
        error_list = ["#DIV/0!", "#ERROR!", "#VALUE!", "#REF!", "#NAME?"]
        df_matrix = df_matrix.replace(error_list, np.nan)

        row_8_data = df_matrix.iloc[8]
        clean_columns_condition = row_8_data.notna()

        df_clean = df_matrix.loc[:, clean_columns_condition]
        df_final = df_clean.T

        df_final.index = timeline[: len(df_final.index)]
        df_final.columns = [
            "Sản lượng",
            "Hàng lỗi",
            "% Hàng lỗi",
            "ĐG + DM",
            "Rỗng",
            "% SL",
            "% Chất lượng",
            "% Hiệu suất",
            "OEE",
        ]
        df_final["plan"] = np.where(
            df_final["% SL"] > 0,
            df_final["Sản lượng"] / df_final["% SL"],
            np.nan,
        )
        df_final["run_time"] = 1440 - df_final["ĐG + DM"]
        df_final = df_final.reset_index().rename(
            columns={"index": "production_day"}
        )
        self.df = df_final

    def write(self):
        self.load()
        paper_oee = PaperDailyOEEWriter(self.influx)
        paper_oee.write_apq(self.df)
