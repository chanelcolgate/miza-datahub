"""Tests for webscraping.evnspc_scraper module"""

import logging

logger = logging.getLogger(__name__)


def test_scrape_data(scraper, debug=True):
    scraper.login()
    data = scraper.scrape_data("29-08-2026", "07-09-2026")

    if debug:
        logger.info(f"Result: {data}")

    result = scraper.write(data)
    assert result is not None
