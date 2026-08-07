"""Tests for the miza_datahub.services.reader_factory module."""

from pathlib import Path

from miza_datahub.common import config_const as ConfigConst
from miza_datahub.services.reader_factory import ReaderFactory

UPLOAD_DIR = Path("data")
UPLOAD_DIR.mkdir(exist_ok=True)


def ignore_test_excel_1(debug=False):
    file_path = UPLOAD_DIR / "Q.xlsx"

    production = ReaderFactory.create(file_path=file_path)
    assert production.write()


def ignore_test_excel_2(debug=False):
    file_path = UPLOAD_DIR / "OEE.xlsx"

    production = ReaderFactory.create(file_path=file_path)
    assert production.write()


def ignore_test_excel_3(debug=False):
    file_path = UPLOAD_DIR / "Air.xlsx"

    production = ReaderFactory.create(file_path=file_path)
    assert production.write()


def ignore_test_excel_4(debug=False):
    file_path = UPLOAD_DIR / "DT.xlsx"

    production = ReaderFactory.create(file_path=file_path)
    assert production.write()


def test_excel_5(config_util, debug=False):
    file_path = config_util.get_property(
        section=ConfigConst.EXCEL, key=ConfigConst.DATA_QUALITY_PATH
    )
    # file_path = (
    #     "https://dongtienpaper-my.sharepoint.com/:x:/p/nguyenthinhu/"
    #     "IQDj5lSaTaPXRZAt5BK4ipTlAc5jW8cwKyZDG1-sz5X0f5o"
    #     "?rtime=byQN_PDx3kg"
    # )
    production = ReaderFactory.create(file_path=file_path)
    assert production.write()
