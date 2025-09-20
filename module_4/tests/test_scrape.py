"""Tests for scrape.py."""

import pytest
from scrape import scrape_page, scrape_data

@pytest.mark.web
def test_scrape_page_robots_denied(mocker):
    """Raise exception if robots.txt denies access."""
    # Force _check_robots_permission to return False
    mocker.patch("scrape._check_robots_permission", return_value=False)
    with pytest.raises(Exception) as excinfo:
        scrape_page(1)
    assert "robots.txt permission check failed" in str(excinfo.value)


@pytest.mark.web
def test_scrape_data_exception(mocker):
    """Return empty list if scrape_page raises an exception."""
    # Patch scrape_page to raise an exception
    mocker.patch("scrape.scrape_page", side_effect=Exception("boom"))
    results = scrape_data(1)
    # Should catch the exception and return an empty list
    assert results == []


@pytest.mark.web
def test_from_soup_exception(mocker, mock_scrape):
    """Return empty list if scrape_page raises an exception."""
    # Patch AdmissionResult.from_soup to raise an exception
    mocker.patch("scrape.AdmissionResult.from_soup", side_effect=Exception("Test parse error"))
    results = scrape_data(1)
    # Should catch the exception and return an empty list
    assert results == []
