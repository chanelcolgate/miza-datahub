"""Tests for the miza_datahub.services.reader_factory module."""

from pathlib import Path

from miza_datahub.services.reader_factory import ReaderFactory

UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)


def test_excel_1(debug=False):
    file_path = UPLOAD_DIR / "Q.xlsx"

    production = ReaderFactory.create(file_path=file_path)
    assert production.write()


def test_excel_2(debug=False):
    file_path = UPLOAD_DIR / "OEE.xlsx"

    production = ReaderFactory.create(file_path=file_path)
    assert production.write()
