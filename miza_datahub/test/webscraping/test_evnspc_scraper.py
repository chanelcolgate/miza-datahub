"""Tests for webscraping.evnspc_scraper module"""

import logging

logger = logging.getLogger(__name__)


def ignore_test_scrape_data(scraper, debug=False):
    scraper.login()
    data = scraper.scrape_data("17-08-2026", "15-09-2026")

    if debug:
        logger.info(f"Result: {data}")

    result = scraper.write(data)
    assert result is not None
