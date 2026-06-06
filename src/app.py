from io import BytesIO

import requests
import pandas as pd
import numpy as np
from fastapi import FastAPI

from miza_datahub.readers.finished_product_quality_analyzer import (
    FinishedProductQualityAnalyzer,
)
from miza_datahub.influxdb.influx_rest_client import InfluxRestClient
from miza_datahub.services.oee_service import OEEService
from miza_datahub.influxdb.queries.paper_machine_query import PaperMachineRepository
from miza_datahub.influxdb.writers.paper_daily_oee_writer import PaperDailyOEEWriter

app = FastAPI()
influx = InfluxRestClient("192.168.10.2", 8090, "miza_new")
paper = PaperMachineRepository(influx)
paper_oee = PaperDailyOEEWriter(influx)


@app.post("/excel")
def read_excel(data: dict):
    file_id = data["file_id"]

    production_quality = FinishedProductQualityAnalyzer(file_id)
    production_quality.load()
    df_quality = production_quality.calculate_defect_weight()

    actual = paper.get_actual_production_daily(
        start_time=(df_quality["production_day"].min()).strftime("%Y-%m-%dT00:00:00Z"),
        end_time=(df_quality["production_day"].max() + pd.Timedelta(days=1)).strftime(
            "%Y-%m-%dT00:00:00Z"
        ),
    )

    plan = paper.get_plan_production_daily(
        start_time=(df_quality["production_day"].min()).strftime("%Y-%m-%dT00:00:00Z"),
        end_time=(df_quality["production_day"].max() + pd.Timedelta(days=1)).strftime(
            "%Y-%m-%dT00:00:00Z"
        ),
    )
    df_final = OEEService.calculate_pq(actual, plan, df_quality)
    paper_oee.write_pq(df_final)

    return df_final.to_dict(orient="records")


@app.get("/daily")
def get_daily_oee(date: str):
    pass
