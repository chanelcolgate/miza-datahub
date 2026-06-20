"""Tests for the influxdb.queries.oee.miza_realtime_query module"""

import logging

logger = logging.getLogger(__name__)


def test_get_daily_availability(miza_realtime_query, debug=False):
    result = miza_realtime_query.get_daily_availability("2026-06-15")
    if debug:
        logger.info("Result = %s", result)

    assert result is not None
    assert isinstance(result, list)


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
