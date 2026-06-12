from abc import ABC, abstractmethod

import requests

from miza_datahub.common.config_util import ConfigUtil
from miza_datahub.common import config_const as ConfigConst
from miza_datahub.influxdb.influx_rest_client import InfluxRestClient


class BaseReader(ABC):
    def __init__(self, file_id=None, file_path=None):
        config_util = ConfigUtil()

        # Telegram
        if file_id:
            token = config_util.get_property(
                section=ConfigConst.TELEGRAM, key=ConfigConst.TOKEN
            )

            r = requests.get(
                ConfigConst.URL_GET_FILE_PATH.format(token=token),
                params={"file_id": file_id},
            ).json()
            if not r.get("ok"):
                raise ValueError(f"Telegram error: {r.get('description')}")

            file_path = r["result"]["file_path"]

            self.file_bytes = requests.get(
                ConfigConst.URL_GET_FILE_CONTENT.format(
                    token=token, file_path=file_path
                )
            ).content

        # file local
        elif file_path:
            with open(file_path, "rb") as f:
                self.file_bytes = f.read()

        # InfluxDB
        influx_host = config_util.get_property(
            section=ConfigConst.INFLUX, key=ConfigConst.INFLUX_HOST, default_val="192.168.10.2"
        )
        influx_port = config_util.get_int(
            section=ConfigConst.INFLUX, key=ConfigConst.INFLUX_PORT, default_val=8090
        )
        influx_db = config_util.get_property(
            section=ConfigConst.INFLUX, key=ConfigConst.INFLUX_DB, default_val="miza_new"
        )
        self.influx = InfluxRestClient(influx_host, influx_port, influx_db)

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def write(self):
        pass


class TempReader(BaseReader):
    def load(self):
        pass

    def write(self):
        pass
