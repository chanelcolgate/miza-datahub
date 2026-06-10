import os
import configparser
import logging

from miza_datahub.common.singleton import Singleton
from miza_datahub.common import config_const as ConfigConst


class ConfigUtil(metaclass=Singleton):
    config_file = ConfigConst.DEFAULT_CONFIG_FILE_NAME
    config_parser = configparser.ConfigParser()
    is_loaded = False

    def __init__(self, config_file: str = None) -> None:
        if config_file is not None:
            self.config_file = config_file

        self._load_config()
        logging.info(f"Creted instance of ConfigUtil: {self}")

    def _load_config(self):
        if os.path.exists(self.config_file):
            logging.info(f"Loading config: {self.config_file}")
            self.config_parser.read(self.config_file)
            self.is_loaded = True
        else:
            logging.info(f"""Can't load {self.config_file}.
                Trying default: {ConfigConst.DEFAULT_CONFIG_FILE_NAME}""")
            self.config_file = ConfigConst.DEFAULT_CONFIG_FILE_NAME
            self.config_parser.read(self.config_file)
            self.is_loaded = True

        logging.debug(f"Config: {self.config_parser.sections()}")

    def _get_config(self, force_reload: bool = False) -> config_parser:
        if not self.is_loaded or force_reload:
            self._load_config()

        return self.config_parser

    def get_property(
        self,
        section: str,
        key: str,
        default_val: str = None,
        force_reload: bool = False,
    ):
        return self._get_config(force_reload).get(
            section, key, fallback=default_val
        )

    def get_float(
        self,
        section: str,
        key: str,
        default_val: float = 0.0,
        force_reload: bool = False,
    ):
        return self._get_config(force_reload).getfloat(
            section, key, fallback=default_val
        )

    def get_int(
        self,
        section: str,
        key: str,
        default_val: int = 0,
        force_reload: bool = False,
    ):
        return self._get_config(force_reload).getint(
            section, key, fallback=default_val
        )
