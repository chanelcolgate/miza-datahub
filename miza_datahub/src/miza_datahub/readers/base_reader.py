from abc import ABC, abstractmethod

import requests
import pandas as pd

from miza_datahub.common.config_util import ConfigUtil
from miza_datahub.common import config_const as ConfigConst


class BaseReader(ABC):
    def __init__(self, file_id):
        config_util = ConfigUtil()

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

        @abstractmethod
        def load(self):
            pass
