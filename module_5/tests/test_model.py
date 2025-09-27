"""Tests for data model and HTML parsing functionality."""

import pytest
from datetime import datetime
from model import _decision_from_soup, _tags_from_soup


@pytest.mark.db
def test_decision_from_soup_invalid_format():
    """Test decision parsing with malformed input string."""
    status, date = _decision_from_soup("INVALID DECISION", 2024)
    assert status is None
    assert date is None


@pytest.mark.db
def test_decision_from_soup_valid_date():
    """Test successful decision string parsing."""
    today_year = datetime.now().year
    status, date = _decision_from_soup("Accepted on 01 Jan", today_year)
    assert status == "accepted"
    assert date.month == 1
    assert date.day == 1


# ------------------------
# _tags_from_soup
# ------------------------


@pytest.mark.db
def test_tags_from_soup_minimal():
    """Test tag parsing with empty input."""
    result = _tags_from_soup(set())
    assert result["season"] is None
    assert result["year"] is None
    assert result["applicant_region"] is False


@pytest.mark.db
def test_tags_from_soup_full():
    """Test comprehensive tag parsing with all data types.
    
    Tests proper data type conversion (strings to floats/ints).
    """
    tags = {"fall 23", "international", "gpa 3.5", "gre 320", "gre v 160", "gre aw 3.5"}
    result = _tags_from_soup(tags)
    assert result["season"] == "fall"
    assert result["year"] == 2023
    assert result["applicant_region"] == "international"
    assert result["gpa"] == 3.5
    assert result["gre_general"] == 320
    assert result["gre_verbal"] == 160
    assert result["gre_analytical_writing"] == 3.5
