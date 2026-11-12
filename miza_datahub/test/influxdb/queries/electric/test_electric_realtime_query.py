import logging

logger = logging.getLogger(__name__)


def test_get_daily_electric(electric_realtime_query, debug=False):
    result = electric_realtime_query.get_daily_electric("2026-08-31")
    if debug:
        logger.info(f"Result: {result}")

    assert result is not None
