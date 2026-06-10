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
from miza_datahub.services.oee_service import OEEService


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
        df_final = OEEService.calculate_pq(actual, plan, df_quality)
        paper_oee.write_pq(df_final)

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
