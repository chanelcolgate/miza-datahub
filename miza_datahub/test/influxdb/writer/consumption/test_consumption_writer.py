"""Test for influxdb.writers.consumption_writer module"""

import logging

logger = logging.getLogger(__name__)


def test_compute_metrics_for_date_minus_1(consumption_writer, debug=False):
    result = consumption_writer.compute_metrics_for_date_minus_1("2026-09-01")

    if debug:
        logger.info(f"Result: {result}")

    assert result["air_consumption"] == 2.25
    assert result["water_consumption"] == 3.43
    assert result["waste_water_consumption"] == 1.61


def test_compute_metrics_for_date_minus_2(consumption_writer, debug=True):
    result = consumption_writer.compute_metrics_for_date_minus_2("2026-09-01")

    if debug:
        logger.info(f"Result: {result}")

    assert result["electric_consumption"] == 474.91


def test_write_for_dates_minus_1(consumption_writer, debug=False):
    consumption_writer.write_for_dates_minus_1(
        ["2026-08-31", "2026-09-01", "2026-09-02"]
    )


def test_write_for_dates_minus_2(consumption_writer, debug=False):
    consumption_writer.write_for_dates_minus_2(
        ["2026-08-31", "2026-09-01", "2026-09-02"]
    )
