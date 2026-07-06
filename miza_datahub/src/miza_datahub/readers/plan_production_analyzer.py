import re
import logging
from io import BytesIO

import pandas as pd
import numpy as np
import openpyxl as op

from miza_datahub.readers.base_reader import BaseReader
from miza_datahub.postgres.writers.plan_production_analyzer import (
    PlanProductionAnalyzerWriter,
)

logger = logging.getLogger(__name__)


class PlanProductionAnalyzer(BaseReader):
    @staticmethod
    def float_hours_to_time_string(float_hours):
        hours = int(float_hours)
        minutes = int((float_hours - hours) * 60)
        seconds = int((((float_hours - hours) * 60) - minutes) * 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def load(self):
        try:
            book = op.load_workbook(BytesIO(self.file_bytes), data_only=True)
            logger.info("Successfully loaded workbook from BytesIO stream.")
        except Exception as e:
            logger.error(f"Failed to load workbook from BytesIO: {e}")
            raise
        sheet_names_sorted = sorted(
            [elem for elem in book.sheetnames if elem.isdigit()], key=int
        )

        all_dfs = []
        for sheet_name in sheet_names_sorted:
            df_raw = pd.read_excel(
                BytesIO(self.file_bytes),
                sheet_name=f"{sheet_name}",
                skiprows=4,
                usecols="B:H,AY:BB",
                names=[
                    "paper_grade",
                    "customer",
                    "gsm_target",
                    "production_total",
                    "speed_target",
                    "production_total_per_hour",
                    "duration",
                    "start_hour",
                    "start_day",
                    "end_hour",
                    "end_day",
                ],
            )
            df_raw = df_raw.dropna(subset=["production_total"])
            df_raw["gsm_target"] = df_raw["gsm_target"].astype(np.uint16)
            df_raw["production_total"] = df_raw["production_total"].astype(
                np.float32
            )
            df_raw["speed_target"] = df_raw["speed_target"].astype(np.uint16)
            df_raw["production_total_per_hour"] = round(
                df_raw["gsm_target"]
                * df_raw["speed_target"]
                * 4.8
                * 60
                / 1000000
                * 0.98,
                2,
            ).astype(np.float32)
            df_raw["duration"] = df_raw["duration"].astype(np.uint8)
            df_raw["start_day"] = df_raw["start_day"].astype(np.uint8)
            df_raw["end_day"] = df_raw["end_day"].astype(np.uint8)

            a1_value = book[sheet_name]["A1"].value

            match = re.search(r"(\d+)/(\d+)/(\d+)", a1_value)

            if match:
                # day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))

                YEAR_MONTH = f"{year}-{month:02d}-"
            else:
                YEAR_MONTH = "2026-06-"

            df_raw["start_time_str"] = df_raw["start_hour"].apply(
                self.float_hours_to_time_string
            )
            df_raw["end_time_str"] = df_raw["end_hour"].apply(
                self.float_hours_to_time_string
            )

            df_raw["start_day_str"] = (
                df_raw["start_day"].astype(int).astype(str)
            )
            df_raw["end_day_str"] = df_raw["end_day"].astype(int).astype(str)

            df_raw["start_time"] = pd.to_datetime(
                YEAR_MONTH
                + df_raw["start_day_str"]
                + " "
                + df_raw["start_time_str"]
            ).dt.tz_localize("Asia/Ho_Chi_Minh")
            df_raw["end_time"] = pd.to_datetime(
                YEAR_MONTH
                + df_raw["end_day_str"]
                + " "
                + df_raw["end_time_str"]
            ).dt.tz_localize("Asia/Ho_Chi_Minh")
            df_raw["start_timestamp"] = (
                df_raw["start_time"].astype("int64") // 10**6
            )
            df_raw["end_timestamp"] = (
                df_raw["end_time"].astype("int64") // 10**6
            )

            df = df_raw[
                [
                    "paper_grade",
                    "customer",
                    "gsm_target",
                    "production_total",
                    "speed_target",
                    "production_total_per_hour",
                    "duration",
                    "start_time",
                    "end_time",
                    "start_timestamp",
                    "end_timestamp",
                ]
            ].copy()

            df["sheet_source"] = sheet_name
            all_dfs.append(df)

        final_df = pd.concat(all_dfs, ignore_index=True)
        final_df.set_index("start_time", inplace=True)
        final_df.sort_index(inplace=True)

        self.df = final_df

    def write(self):
        self.load()
        plan_production = PlanProductionAnalyzerWriter(
            host=self.timescaledb_host,
            port=self.timescaledb_port,
            database=self.timescaledb_db,
            username=self.timescaledb_usr,
            password=self.timescaledb_pass,
        )
        plan_production.write_data(self.df)
        return True
