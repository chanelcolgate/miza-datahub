"""Tests for the influxdb.queries.oee.miza_realtime_query module"""

import logging
from datetime import datetime

from miza_datahub.common import config_const as ConfigConst  # type: ignore
from miza_datahub.services.oee_service import OEEService  # type: ignore

logger = logging.getLogger(__name__)


def test_get_daily_availability(miza_realtime_query, debug=False):
    result = miza_realtime_query.get_daily_availability("2026-06-15")
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_realtime_availability(miza_realtime_query, debug=False):
    now_vn = datetime.now(ConfigConst.VN_TZ)
    current_date_str = now_vn.strftime("%Y-%m-%d")
    result = miza_realtime_query.get_daily_availability(current_date_str)
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_daily_performance(miza_realtime_query, debug=False):
    now_vn = datetime.now(ConfigConst.VN_TZ)
    current_date_str = now_vn.strftime("%Y-%m-%d")
    result = miza_realtime_query.get_daily_performance(current_date_str)
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_last_speed(miza_realtime_query, debug=True):
    availability = miza_realtime_query.get_daily_availability()
    performance = miza_realtime_query.get_daily_performance()
    last_speed = miza_realtime_query.get_last_speed()
    result = OEEService().merge_metrics_to_dict_list(
        availability, performance, last_speed
    )
    if debug:
        logger.info(f"Result: {result}")


def test_get_daily_availability_no_data(miza_realtime_query, debug=False):
    result = miza_realtime_query.get_daily_availability("2099-01-01")
    if debug:
        logger.info(f"Result = {result}")

    assert len(result) == 0


def test_get_monthly_availablity(miza_realtime_query, debug=False):
    result = miza_realtime_query.get_monthly_availability(year=2026, month=6)
    if debug:
        logger.info(f"Result = {result}")

    assert result is not None
    assert isinstance(result, float)


def test_get_monthly_availablity_no_data(miza_realtime_query, debug=False):
    result = miza_realtime_query.get_monthly_availability(year=2099, month=1)
    if debug:
        logger.info(f"Result = {result}")

    assert result is None


def test_get_yearly_availability(miza_realtime_query, debug=False):
    result = miza_realtime_query.get_yearly_availability(year=2026)
    if debug:
        logger.info(f"Result = {result}")

    assert result is not None
    assert isinstance(result, float)


def test_get_availability_trend(miza_realtime_query, debug=False):
    for interval in ["1h", "1d", "30d"]:
        result = miza_realtime_query.get_availability_trend(
            start_time="2026-06-01T06:00:00+07:00",
            end_time="2026-06-17T06:00:00+07:00",
            interval=interval,
        )
        if debug:
            logger.info(f"Result = {result}")

        assert result is not None
        assert isinstance(result, list)
