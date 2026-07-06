from io import BytesIO

import pandas as pd

from miza_datahub.readers.base_reader import TempReader
from miza_datahub.readers.oee_analyzer import OEEAnalyzer
from miza_datahub.readers.quality_analyzer import (
    QualityAnalyzer,
)
from miza_datahub.readers.plan_production_analyzer import PlanProductionAnalyzer


def detect_file_types(file_bytes):
    excel = pd.ExcelFile(BytesIO(file_bytes))
    sheets = excel.sheet_names

    if "OEE" in sheets:
        return "oee"

    if "Chi_Tiet_Chat_Luong" in sheets:
        return "quality"

    if "3_ĐKSX_OK" in sheets:
        return "plan"

    return ValueError(f"Don't read file. Sheets={sheets}")


class ReaderFactory:
    @staticmethod
    def create(file_id=None, file_path=None):
        base = TempReader(file_id=file_id, file_path=file_path)

        file_type = detect_file_types(base.file_bytes)

        if file_type == "oee":
            return OEEAnalyzer(file_id=file_id, file_path=file_path)

        if file_type == "quality":
            return QualityAnalyzer(file_id=file_id, file_path=file_path)

        if file_type == "plan":
            return PlanProductionAnalyzer(file_id=file_id, file_path=file_path)
