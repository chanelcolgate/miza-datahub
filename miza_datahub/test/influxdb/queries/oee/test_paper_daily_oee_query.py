"""Tests for the influxdb.queries.ooe.paper_daily_oee_query module"""

import logging

logger = logging.getLogger(__name__)


def test_get_daily_all_values(paper_daily_oee_query, debug=False):
    result = paper_daily_oee_query.get_daily_all_values("2026-06-15")
    if debug:
        logger.info(f"Result = {result}")

    assert result is not None


def test_get_monthly_all_values(paper_daily_oee_query, debug=False):
    result = paper_daily_oee_query.get_monthly_all_values(year=2026, month=6)
    if debug:
        logger.info(f"Result = {result}")

    assert result is not None


def test_get_yearly_all_values(paper_daily_oee_query, debug=False):
    result = paper_daily_oee_query.get_yearly_all_values(year=2026)
    if debug:
        logger.info(f"Result = {result}")

    assert result is not None


def test_get_all_values_trend(paper_daily_oee_query, debug=False):
    for interval in ["1d", "30d"]:
        result = paper_daily_oee_query.get_all_values_trend(
            start_time="2026-06-01T06:00:00+07:00",
            end_time="2026-06-30T06:00:00+07:00",
            interval=interval,
        )

        if debug:
            logger.info(f"Result = {result}")

    assert result is not None


# def test_delete_all_values_error(paper_daily_oee_query, debug=True):
#     result = paper_daily_oee_query.delete_all_values_error()
#     if debug:
#         logger.info(f"Result = {result}")
#
#     assert result is not None
