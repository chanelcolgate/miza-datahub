import logging

logger = logging.getLogger(__name__)


def test_get_hourly_water(water_realtime_query, debug=False):
    result = water_realtime_query.get_daily_water("2026-06-24", "1h")
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_hourly_water_2(water_realtime_query, debug=False):
    result = water_realtime_query.get_daily_water(interval="1h")

    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_daily_water(water_realtime_query, debug=False):
    result = water_realtime_query.get_daily_water("2026-06-24", "1d")
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_daily_water_2(water_realtime_query, debug=False):
    result = water_realtime_query.get_daily_water()
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_monthly_water(water_realtime_query, debug=False):
    result = water_realtime_query.get_monthly_water(
        year=2026, month=6, interval="1d"
    )
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_monthly_water_2(water_realtime_query, debug=False):
    result = water_realtime_query.get_monthly_water(
        year=2026, month=6, interval="1mo"
    )
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None


def test_get_yearly_water(water_realtime_query, debug=False):
    result = water_realtime_query.get_monthly_water(year=2026, interval="y")
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None
