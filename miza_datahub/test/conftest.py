import logging

import pytest

from miza_datahub.common.config_util import ConfigUtil
from miza_datahub.common import config_const as ConfigConst
from miza_datahub.influxdb.influx_rest_client import InfluxRestClient
from miza_datahub.influxdb.queries.oee.miza_realtime_query import (
    MizaRealtimeQuery,
)
from miza_datahub.influxdb.queries.oee.paper_daily_oee_query import (
    PaperDailyOEEQuery,
)
from miza_datahub.influxdb.queries.pulp.pulp_realtime_query import (
    PulpRealtimeQuery,
)
from miza_datahub.influxdb.queries.air.air_realtime_query import (
    AirRealtimeQuery,
)
from miza_datahub.influxdb.queries.water.water_realtime_query import (
    WaterRealtimeQuery,
)
from miza_datahub.postgres.queries.electricity_consumption_query import (
    ElectricityConsumptionQuery,
)
from miza_datahub.webscraping.evnspc_scraper import EVNSPCScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)

collect_ignore = ["path/to/test/excluded"]
collect_ignore_glob = ["*_ignore.py"]


@pytest.fixture(scope="session")
def config_util():
    return ConfigUtil()


@pytest.fixture(scope="session")
def influx(config_util):
    influx_host = config_util.get_property(
        section=ConfigConst.INFLUX,
        key=ConfigConst.INFLUX_HOST,
        default_val="192.168.10.2",
    )
    influx_port = config_util.get_int(
        section=ConfigConst.INFLUX,
        key=ConfigConst.INFLUX_PORT,
        default_val=8090,
    )
    influx_db = config_util.get_property(
        section=ConfigConst.INFLUX,
        key=ConfigConst.INFLUX_DB,
        default_val="miza_new",
    )
    return InfluxRestClient(influx_host, influx_port, influx_db)


@pytest.fixture(scope="session")
def miza_realtime_query(influx):
    return MizaRealtimeQuery(influx)


@pytest.fixture(scope="session")
def paper_daily_oee_query(influx):
    return PaperDailyOEEQuery(influx)


@pytest.fixture(scope="session")
def pulp_realtime_query(influx):
    return PulpRealtimeQuery(influx)


@pytest.fixture(scope="session")
def air_realtime_query(influx):
    return AirRealtimeQuery(influx)


@pytest.fixture(scope="session")
def water_realtime_query(influx):
    return WaterRealtimeQuery(influx)


@pytest.fixture(scope="session")
def electricity_consumption_query(config_util):
    postgres_host = config_util.get_property(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_HOST,
        default_val="172.26.2.13",
    )
    postgres_port = config_util.get_int(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_PORT,
        default_val=5432,
    )
    postgres_db = config_util.get_property(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_DB,
        default_val="tb-edge",
    )
    username = config_util.get_property(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_USERNAME,
        default_val="postgres",
    )
    password = config_util.get_property(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_PASSWORD,
        default_val="postgres",
    )
    return ElectricityConsumptionQuery(
        host=postgres_host,
        port=postgres_port,
        database=postgres_db,
        username=username,
        password=password,
    )


@pytest.fixture(scope="session")
def scraper():
    scraper_instance = EVNSPCScraper(headless=True)
    yield scraper_instance
    scraper_instance.close()
