import logging

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from miza_datahub.common.config_util import ConfigUtil
from miza_datahub.common import config_const as ConfigConst
from miza_datahub.influxdb.influx_rest_client import InfluxRestClient
from miza_datahub.influxdb.queries.oee.miza_realtime_query import (
    MizaRealtimeQuery,
)
from miza_datahub.influxdb.queries.oee.paper_daily_oee_query import (
    PaperDailyOEEQuery,
)
from miza_datahub.influxdb.writers.paper_daily_oee_writer import (
    PaperDailyOEEWriter,
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
from miza_datahub.influxdb.queries.electric.electric_realtime_query import (
    ElectricRealtimeQuery,
)
from miza_datahub.postgres.queries.electricity_consumption_query import (
    ElectricityConsumptionQuery,
)
from miza_datahub.webscraping.evnspc_scraper import EVNSPCScraper
from miza_datahub.influxdb.writers.consumption_writer import ConsumptionWriter
from miza_datahub.influxdb.queries.oee.dongtien_realtime_query import (
    DongTienRealtimeQuery,
)
from miza_datahub.postgres.writers.daily_production_reports import (
    DailyProductionReports,
)
from miza_datahub.postgres.postgres_repository import PostgresRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)

collect_ignore = ["path/to/test/excluded"]
collect_ignore_glob = ["*_ignore.py"]

TEST_DATABASE_URL = "postgresql+psycopg2://odoo:odoo@localhost:32768/monitoring"


@pytest.fixture(scope="session")
def config_util():
    return ConfigUtil()


@pytest.fixture(scope="session")
def influx(config_util):
    influx_host = config_util.get_property(
        section=ConfigConst.INFLUX,
        key=ConfigConst.INFLUX_HOST,
        default_val="localhost",
    )
    influx_port = config_util.get_int(
        section=ConfigConst.INFLUX,
        key=ConfigConst.INFLUX_PORT,
        default_val=8090,
    )
    influx_db = config_util.get_property(
        section=ConfigConst.INFLUX,
        key=ConfigConst.INFLUX_DB,
        default_val="dongtien",
    )
    return InfluxRestClient(influx_host, influx_port, influx_db)


@pytest.fixture(scope="session")
def miza_realtime_query(influx):
    return MizaRealtimeQuery(influx)


@pytest.fixture(scope="session")
def paper_daily_oee_query(influx):
    return PaperDailyOEEQuery(influx)


@pytest.fixture(scope="session")
def paper_daily_oee_writer(influx):
    return PaperDailyOEEWriter(influx)


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
def electric_realtime_query(influx):
    return ElectricRealtimeQuery(influx)


@pytest.fixture(scope="session")
def consumption_writer(influx):
    return ConsumptionWriter(influx)


@pytest.fixture(scope="session")
def dongtien_realtime_query(influx):
    return DongTienRealtimeQuery(influx)


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


@pytest.fixture(scope="session")
def db_engine():
    engine = sa.create_engine(TEST_DATABASE_URL)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="session")
def pg_repo(config_util):
    postgres_host = config_util.get_property(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_HOST,
        default_val="localhost",
    )
    postgres_port = config_util.get_int(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_PORT,
        default_val=32768,
    )
    postgres_db = config_util.get_property(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_DB,
        default_val="monitoring",
    )
    username = config_util.get_property(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_USERNAME,
        default_val="odoo",
    )
    password = config_util.get_property(
        section=ConfigConst.POSTGRES,
        key=ConfigConst.POSTGRES_PASSWORD,
        default_val="postgres",
    )
    return PostgresRepository(
        host=postgres_host,
        port=postgres_port,
        database=postgres_db,
        username=username,
        password=password,
    )


@pytest.fixture(scope="session")
def daily_production_reports(pg_repo, influx):
    return DailyProductionReports(pg_repo, influx)
