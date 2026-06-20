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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

loggerr = logging.getLogger(__name__)


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
