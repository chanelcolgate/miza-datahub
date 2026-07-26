import logging
from io import BytesIO

import numpy as np
import pandas as pd

from miza_datahub.readers.base_reader import BaseReader
from miza_datahub.influxdb.queries.paper_machine_query import (
    PaperMachineRepository,
)
from miza_datahub.influxdb.writers.paper_daily_oee_writer import (
    PaperDailyOEEWriter,
)
from miza_datahub.influxdb.writers.quality_analyzer import (
    JumboRollWriter,
    CutRollWriter,
)
from miza_datahub.services.oee_service import OEEService

logger = logging.getLogger(__name__)


class QualityAnalyzer(BaseReader):
    def load(self):
        df = pd.read_excel(
            BytesIO(self.file_bytes),
            sheet_name="Chi_Tiet_Chat_Luong",
            skiprows=5,
            usecols="C:F,H:O,AA:AF,AO:AZ,BB:BF",
            names=[
                "Ngày SX",
                "Loại Giấy",
                "Khách hàng",
                "Trưởng ca",
                "Mã cuộn",
                "Ngày cắt cuộn",
                "Giờ ra quả Xeo",
                "Khổ giấy (cm)",
                "Tổng khổ (cm)",
                "Định lượng YC (g/m2)",
                "Định lượng TB (g/m2)",
                "Định lượng TT (g/m2)",
                "Số vết nối TT",
                "Số vết nối YC",
                "Độ bục TB",
                "Cường độ bục TT",
                "Độ bục YC",
                "Cường độ bục YC",
                "Độ nhẵn (s)",
                "Chống thấm YC",
                "Chiều dài cuộn (m)",
                "Chiều dài cuộn theo CT",
                "Đánh giá chiều dài cuộn",
                "Trọng lượng (kg)",
                "Người đóng gói",
                "Nhân viên QC",
                "Độ dương khổ (mm)",
                "Đường kính quả",
                "Ghi Chú",
                "Mã quả Xeo",
                "Loại CL",
                "Chỉ số màu L*",
                "Chỉ số màu a*",
                "Chỉ số màu b*",
                "Loại SP",
            ],
        )

        # 1. Chuẩn hóa giờ: đổi ; thành :
        df["Giờ ra quả Xeo"] = (
            df["Giờ ra quả Xeo"].astype(str).str.replace(";", ":", regex=False)
        )

        # 2. Loại bỏ NaN / NaT / chuỗi lỗi
        df = df[df["Giờ ra quả Xeo"].notna()]
        df = df[df["Giờ ra quả Xeo"].str.lower() != "nat"]

        # 3. Tạo datetime
        df["Thời điểm ra quả xeo"] = pd.to_datetime(
            df["Ngày SX"].astype(str) + " " + df["Giờ ra quả Xeo"],
            errors="coerce",
        )

        # 4. Loại bỏ dòng parse lỗi lần cuối
        df = df.dropna(subset=["Thời điểm ra quả xeo"])

        df = df.set_index(["Thời điểm ra quả xeo", "Mã cuộn", "Ngày cắt cuộn"])
        # df["Mã quả Xeo"] = df["Mã quả Xeo"].astype(np.uint32)
        self.df = df

    def write(self):
        self.load()
        df_quality = self.calculate_defect_weight()

        paper = PaperMachineRepository(self.influx)
        paper_oee = PaperDailyOEEWriter(self.influx)

        actual = paper.get_actual_production_daily(
            start_time=(df_quality["production_day"].min()).strftime(
                "%Y-%m-%dT00:00:00Z"
            ),
            end_time=(
                df_quality["production_day"].max() + pd.Timedelta(days=1)
            ).strftime("%Y-%m-%dT00:00:00Z"),
        )

        plan = paper.get_plan_production_daily(
            start_time=(df_quality["production_day"].min()).strftime(
                "%Y-%m-%dT00:00:00Z"
            ),
            end_time=(
                df_quality["production_day"].max() + pd.Timedelta(days=1)
            ).strftime("%Y-%m-%dT00:00:00Z"),
        )
        df_final = OEEService.calculate_pq(actual, plan, df_quality, mode="Q")
        paper_oee.write_pq(df_final)
        return True

    def calculate_defect_weight(self):
        time_idx = self.df.index.get_level_values("Thời điểm ra quả xeo")
        quality_df = (
            self.df.assign(
                production_day=(time_idx - pd.Timedelta(hours=6)).floor("D")
            )
            .groupby(["production_day", "Loại CL"])["Trọng lượng (kg)"]
            .sum()
            .unstack(fill_value=0)
        )

        quality_df = quality_df.reset_index()
        # quality_df["scrap_kg"] = quality_df.get("B", 0)
        # quality_df["good_kg"] = quality_df.get("A", 0)
        # print(quality_df)
        return quality_df

    def summarize_columns(self):
        print(f"{'Column':35} {'Type':15} {'Unique':>10} {'Memory(MB)':>12}")
        print("-" * 75)

        for c in self.df.columns:
            print(
                f"{c:35} "
                f"{str(self.df[c].dtype):15} "
                f"{self.df[c].nunique(dropna=False):>10,} "
                f"{self.df[c].memory_usage(deep=True)/1024**2:>12.2f}"
            )
        self.df.info(memory_usage="deep")


class JumboRollAnalyzer(BaseReader):
    def load(self):
        try:
            df = pd.read_excel(
                BytesIO(self.file_bytes),
                sheet_name="TH",
                skiprows=3,
                usecols="B:I,P,W,AE,BQ",
                names=[
                    "Giờ",
                    "Loại giấy",
                    "Định lượng chuẩn",
                    "Ngày cắt cuộn con",
                    "Khổ",
                    "Khách hàng",
                    "Mã cuộn",
                    "Khối lượng",
                    "Định lượng trung bình",
                    "Bục trung bình",
                    "Nén vòng trung bình",
                    "Ca cắt",
                ],
            )
        except Exception as e:
            logger.error(f"Failed to load workbook from BytesIO: {e}")
            raise

        df = df.dropna(subset=["Mã cuộn"])

        df["Mã cuộn"] = df["Mã cuộn"].astype(str).str.strip()
        code_date_str = df["Mã cuộn"].str[3:9]

        code_datetime = pd.to_datetime(
            code_date_str, format="%d%m%y", errors="coerce"
        )
        date_str = code_datetime.dt.strftime("%Y-%m-%d")

        df["Giờ"] = df["Giờ"].ffill().fillna("0h00")

        time_str = (
            df["Giờ"]
            .astype(str)
            .str.replace(r"[^0-9h]", "", regex=True)  # ' ~2h ' -> '2h'
            .str.replace(r"h$", "h00", regex=True)  # '2h' -> '2h00'
            .str.replace("h", ":", regex=False)  # '2h00' -> '2:00'
            .str.replace(r"h^24:", "00:", regex=True)  # '24:00' -> '00:00'
        )

        df["jumbo_prod_time"] = pd.to_datetime(
            date_str + " " + time_str, errors="coerce"
        )

        df["Ngày cắt cuộn con"] = pd.to_datetime(
            df["Ngày cắt cuộn con"], dayfirst=True, errors="coerce"
        ).fillna(df["jumbo_prod_time"])

        df["Khối lượng"] = (
            df["Khối lượng"]
            .astype(str)
            .str.replace(r"[^0-9.]", "", regex=True)
            .replace("", np.nan)
            .fillna(0)
            .astype(float)
            .astype(np.uint16)
        )

        df["Định lượng chuẩn"] = (
            df["Định lượng chuẩn"]
            .astype(str)
            .str.replace(r"[^0-9.]", "", regex=True)
            .replace("", np.nan)
            .fillna(0)
            .astype(float)
            .astype(np.uint8)
        )

        kho_clean = (
            df["Khổ"]
            .astype(str)
            .str.replace(r"[^0-9.]", "", regex=True)
            .replace("", np.nan)
            .astype(float)
        )
        df["Khổ"] = (np.round(kho_clean * 2) / 2).astype(np.float32)

        quality_cols = [
            "Định lượng trung bình",
            "Bục trung bình",
            "Nén vòng trung bình",
        ]

        for col in quality_cols:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"[^0-9.]", "", regex=True)
                .replace("", np.nan)
                .fillna(0.0)
                .astype(np.float32)
            )

        df["Ca cắt"] = df["Ca cắt"].ffill().astype(str).str.strip()
        df["Mã cuộn"] = df["Mã cuộn"].astype(str).str.strip()
        df["Khách hàng"] = df["Khách hàng"].astype(str).str.strip()

        df["jumbo_prod_time"] = df["jumbo_prod_time"].fillna(code_datetime)
        df["Ngày cắt cuộn con"] = df["Ngày cắt cuộn con"].fillna(
            df["jumbo_prod_time"]
        )

        df.drop(columns=["Giờ"], inplace=True)

        df_final = df.sort_values(by="jumbo_prod_time").reset_index(drop=True)

        df_final["jumbo_crew"] = df_final["Mã cuộn"].str[0]

        df_final["jumbo_id"] = (
            df_final["Mã cuộn"].str[3:9] + "_" + df_final["Mã cuộn"].str[9:11]
        )

        change_crew = (
            df_final["jumbo_crew"] != df_final["jumbo_crew"].shift(1)
        ).astype(int)
        group_id_temp = change_crew.cumsum()

        start_hour = (
            df_final.groupby(group_id_temp)["jumbo_prod_time"]
            .transform("min")
            .dt.hour
        )
        df_final["jumbo_shift"] = np.where(
            (start_hour >= 6) & (start_hour < 18), "Ca 1", "Ca 2"
        )

        self.df = df_final

    def write(self):
        self.load()

        jumbo_roll_writer = JumboRollWriter(self.influx)
        cut_roll_writer = CutRollWriter(self.influx)

        jumbo_roll_writer.write(self.df)
        cut_roll_writer.write(self.df)
        return True
