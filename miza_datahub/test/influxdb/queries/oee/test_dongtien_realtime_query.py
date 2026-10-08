"""Tests for the influxdb.queries.oee.dongtien_realtime_query module"""

import logging

logger = logging.getLogger(__name__)


def test_get_shift_status_1(dongtien_realtime_query, debug=False):
    result = dongtien_realtime_query.get_shift_status("2026-10-04")
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_shift_status_2(dongtien_realtime_query, debug=False):
    result = dongtien_realtime_query.get_shift_status("2026-10-04", 2)
    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_shift_status_3(dongtien_realtime_query, debug=True):
    result = dongtien_realtime_query.get_shift_status("2026-09-11")
    if debug:
        logger.info("Result = %s", result)

    assert result is not None
