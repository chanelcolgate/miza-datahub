import shutil
from io import BytesIO
from pathlib import Path

import requests
import pandas as pd
import numpy as np
from fastapi import FastAPI, UploadFile, File

from miza_datahub.services.reader_factory import ReaderFactory

app = FastAPI()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@app.post("/excel/read")
def read_excel(data: dict):
    file_id = data["file_id"]

    production = ReaderFactory.create(file_id=file_id)
    production.write()

    return {"status": "success"}


@app.post("/excel/upload")
def save_excel(file: UploadFile = File(...)):
    if not file.filename.endswith((".xlsx", ".xls")):
        return {"error": "Only Excel files are allowed"}

    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    production = ReaderFactory.create(file_path=file_path)
    production.write()

    return {"status": "success", "filename": file.filename, "path": str(file_path)}


@app.get("/daily")
def get_daily_oee(date: str):
    pass
