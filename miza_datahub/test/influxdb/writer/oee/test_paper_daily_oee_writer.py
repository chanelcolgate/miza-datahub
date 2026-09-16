"""Tests for influxdb.writers.paper_daily_oee_writer module"""

import logging

logger = logging.getLogger(__name__)


def test_compute_metrics_for_date_success(paper_daily_oee_writer, debug=False):
    result = paper_daily_oee_writer.compute_metrics_for_date("2026-08-31")
    if debug:
        logger.info(f"Result: {result}")

    assert result["actual"] == 317.19
    assert result["plan"] == 323.25
    assert result["defect"] == 0.0
    assert result["run_time"] == 1440.0
    assert result["down_time"] == 0.0
    assert result["A"] == 100
    assert result["P"] == 97.14
    assert result["Q"] == 100
    assert result["OEE"] == 97.14


def test_write_for_dates_line_protocol(paper_daily_oee_writer, debug=False):
    paper_daily_oee_writer.write_for_dates(
        ["2026-08-31", "2026-09-01", "2026-09-02"]
    )
