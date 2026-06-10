from io import BytesIO

import requests
import pandas as pd
import numpy as np
from fastapi import FastAPI

from miza_datahub.readers.quality_analyzer import (
    QualityAnalyzer,
)
from miza_datahub.influxdb.influx_rest_client import InfluxRestClient
from miza_datahub.influxdb.queries.paper_machine_query import PaperMachineRepository
from miza_datahub.influxdb.writers.paper_daily_oee_writer import PaperDailyOEEWriter
from miza_datahub.services.oee_service import OEEService
from miza_datahub.services.reader_factory import ReaderFactory

app = FastAPI()
influx = InfluxRestClient("192.168.10.2", 8090, "miza_new")
paper = PaperMachineRepository(influx)
paper_oee = PaperDailyOEEWriter(influx)


@app.post("/excel")
def read_excel(data: dict):
    file_id = data["file_id"]

    production = ReaderFactory.create(file_id)
    production.write()

    return {"result": "ok"}


@app.get("/daily")
def get_daily_oee(date: str):
    pass
