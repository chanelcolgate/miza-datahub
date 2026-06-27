"""Tests for influx.queries.air.air_realtime_query module"""

import logging

logger = logging.getLogger(__name__)


def test_get_hourly_air(air_realtime_query, debug=False):
    result = air_realtime_query.get_daily_air("2026-06-24", "1h")
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_hourly_air_2(air_realtime_query, debug=False):
    result = air_realtime_query.get_daily_air(interval="1h")
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_daily_air(air_realtime_query, debug=False):
    result = air_realtime_query.get_daily_air("2026-06-24", "1d")
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_daily_air_2(air_realtime_query, debug=False):
    result = air_realtime_query.get_daily_air()
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_monthly_air(air_realtime_query, debug=False):
    result = air_realtime_query.get_monthly_air(
        year=2026, month=6, interval="1d"
    )
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_monthly_air_2(air_realtime_query, debug=False):
    result = air_realtime_query.get_monthly_air(
        year=2026, month=6, interval="1mo"
    )
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_yearly_air(air_realtime_query, debug=False):
    result = air_realtime_query.get_monthly_air(year=2026, interval="y")
    if debug:
        logger.info(f"Result: {result}")
