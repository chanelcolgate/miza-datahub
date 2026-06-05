from io import BytesIO

import requests
import pandas as pd
import numpy as np
from fastapi import FastAPI

from miza_datahub.readers.finished_product_quality_analyzer import (
    FinishedProductQualityAnalyzer,
)
from miza_datahub.influxdb.queries.paper_machine_query import PaperMachineRepository
from miza_datahub.influxdb.influx_rest_client import InfluxRestClient

app = FastAPI()
influx = InfluxRestClient("192.168.10.2", 8090, "miza_new")
paper = PaperMachineRepository(influx)


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

    df_actual = pd.DataFrame(actual, columns=["time", "actual"])
    df_actual["production_day"] = (
        pd.to_datetime(df_actual["time"]).dt.tz_localize(None).dt.date
    )
    df_actual["production_day"] = pd.to_datetime(df_actual["production_day"])

    df_plan = pd.DataFrame(plan, columns=["time", "plan"])
    df_plan["production_day"] = (
        pd.to_datetime(df_plan["time"]).dt.tz_localize(None).dt.date
    )
    df_plan["production_day"] = pd.to_datetime(df_plan["production_day"])

    df_final = (
        df_actual[["production_day", "actual"]]
        .merge(df_quality[["production_day", "B"]], on="production_day", how="outer")
        .merge(df_plan[["production_day", "plan"]], on="production_day", how="left")
    )

    df_final["P"] = (df_final["actual"] / df_final["plan"] * 100).round(2)
    df_final["Q"] = (
        (df_final["actual"] - df_final["B"] / 1000) / df_final["actual"] * 100
    ).round(2)

    df_final = df_final.replace([np.inf, -np.inf], np.nan)

    df_final = df_final.astype(object)
    df_final = df_final.where(pd.notnull(df_final), None)
    print(df_final)
    return df_final.to_dict(orient="records")
