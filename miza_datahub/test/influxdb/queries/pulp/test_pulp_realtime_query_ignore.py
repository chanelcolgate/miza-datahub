"""Tests for the influx.queries.pulp.pulp_realtime_query module"""

import logging

logger = logging.getLogger(__name__)


def test_get_hourly_pulp(pulp_realtime_query, debug=False):
    result = pulp_realtime_query.get_daily_pulp("2026-06-15", "1h")
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_hourly_pulp_2(pulp_realtime_query, debug=False):
    result = pulp_realtime_query.get_daily_pulp(interval="1h")
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_daily_pulp(pulp_realtime_query, debug=False):
    result = pulp_realtime_query.get_daily_pulp(
        date="2026-06-24", interval="1d"
    )
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_daily_pulp_2(pulp_realtime_query, debug=False):
    result = pulp_realtime_query.get_daily_pulp(interval="1d")
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_monthly_pulp(pulp_realtime_query, debug=False):
    result = pulp_realtime_query.get_monthly_pulp(
        year=2026, month=6, interval="1d"
    )
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_monthly_pulp_2(pulp_realtime_query, debug=True):
    result = pulp_realtime_query.get_monthly_pulp(
        year=2026, month=6, interval="1mo"
    )
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_yearly_pulp(pulp_realtime_query, debug=True):
    result = pulp_realtime_query.get_monthly_pulp(year=2026, interval="y")
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None
