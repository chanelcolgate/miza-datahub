from io import BytesIO
from calendar import monthrange

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
        max_day = monthrange(year, month)[1]
        for marker in time_markers:
            current_day = int(marker)

            if not 1 <= current_day <= max_day:
                continue
            full_timestamp = pd.to_datetime(
                f"{current_day}/{month}/{year} 06:00", dayfirst=True
            )
            timeline.append(full_timestamp)

        df_matrix = df_raw.iloc[1:10, 2:]
        # error_list = ["#DIV/0!", "#ERROR!", "#VALUE!", "#REF!", "#NAME?"]
        df_matrix = df_matrix.replace(
            {
                "#DIV/0!": 0,
                "#ERROR!": np.nan,
                "#VALUE!": np.nan,
                "#REF!": np.nan,
                "#NAME?": np.nan,
            }
        )

        production_row = df_matrix.iloc[8]
        last_valid_col = production_row.last_valid_index()

        df_clean = df_matrix.loc[:, :last_valid_col]
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
        df_final["ĐG + DM"] = df_final["ĐG + DM"].fillna(0)
        df_final["run_time"] = 1440 - df_final["ĐG + DM"]
        df_final = df_final.reset_index().rename(
            columns={"index": "production_day"}
        )
        self.df = df_final

    def write(self):
        self.load()
        paper_oee = PaperDailyOEEWriter(self.influx)
        paper_oee.write_apq(self.df)
        return True
