import logging

logger = logging.getLogger(__name__)


def test_get_daily_consumption_by_device(
    electricity_consumption_query, debug=False
):

    result = electricity_consumption_query.get_daily_consumption_by_device(
        date_str="2026-06-21"
    )

    if debug:
        logger.info("Result = %s", result)

    assert result is not None


def test_get_monthly_consumption_by_device(
    electricity_consumption_query, debug=False
):
    result = electricity_consumption_query.get_montly_consumption_by_device(
        month=6, year=2026
    )

    if debug:
        logger.info(f"Result: {result}")
    assert result is not None


def test_get_yearly_consumption_by_device(
    electricity_consumption_query, debug=False
):
    result = electricity_consumption_query.get_yearly_consumption_by_device(
        year=2026
    )

    if debug:
        logger.info(f"Result: {result}")
    assert result is not None


def test_get_daily_consumption_by_shift(
    electricity_consumption_query, debug=False
):
    result = electricity_consumption_query.get_daily_consumption_by_shift(
        date_str="2026-06-21"
    )

    if debug:
        logger.info(f"Result: {result}")
    assert result is not None


def test_get_daily_consumption_by_shift_1(
    electricity_consumption_query, debug=False
):
    result = electricity_consumption_query.get_daily_consumption_by_shift(
        date_str="2026-06-21", shift=1
    )

    if debug:
        logger.info(f"Result: {result}")
    assert result is not None


def test_get_daily_consumption_by_shift_2(
    electricity_consumption_query, debug=False
):
    result = electricity_consumption_query.get_daily_consumption_by_shift(
        date_str="2026-06-21", shift=2
    )

    if debug:
        logger.info(f"Result: {result}")
    assert result is not None


def test_get_daily_consumption_by_shift_3(
    electricity_consumption_query, debug=False
):
    result = electricity_consumption_query.get_daily_consumption_by_shift(
        date_str="2026-06-21", shift=3
    )

    if debug:
        logger.info(f"Result: {result}")
    assert result is not None


def test_get_daily_consumption_by_timestamp(
    electricity_consumption_query, debug=False
):
    start_timestamp = 1782001332000
    end_timestamp = 1782087732000
    result = electricity_consumption_query.get_daily_consumption_by_timestamp(
        start_timestamp, end_timestamp
    )

    if debug:
        logger.info(f"Result: {result}")
    assert result is not None
