"""Tests for the influxdb.queries.oee.paper_daily_oee_query module"""

import logging

logger = logging.getLogger(__name__)


def test_get_cut_roll_production(paper_daily_oee_query, debug=True):
    cut_roll_production = paper_daily_oee_query.get_cut_roll_production(
        "2026-09-01"
    )
    roll_production = paper_daily_oee_query.get_roll_production("2026-09-02")
    nominal_production = paper_daily_oee_query.get_nominal_production(
        "2026-09-02"
    )
    availability = paper_daily_oee_query.get_availability("2026-09-02")
    if debug:
        logger.info(f"cut_roll_production={cut_roll_production}")
        logger.info(f"roll_production={roll_production}")
        logger.info(f"nominal_production={nominal_production}")
        logger.info(f"availability={availability}")

    assert roll_production is not None


def test_create_paper_daily_oee(paper_daily_oee_query, debug=True):
    oee, run_time_min, downtime_min = (
        paper_daily_oee_query.create_paper_daily_oee("2026-09-02")
    )

    if debug:
        logger.info(f"oee={oee}")
        logger.info(f"run_time_min={run_time_min}")
        logger.info(f"downtime_min={downtime_min}")

    assert oee is not None
