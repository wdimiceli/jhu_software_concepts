"""Tests for database writes and query operations.

This module tests database insertion, idempotency constraints, and query
functions to ensure data integrity and proper schema compliance.
"""

import pytest
from model import AdmissionResult, get_table


# a. Test insert on pull
# i. Before: target table empty
# ii. After POST/pull-data new rows exist with required (non-null) fields


@pytest.mark.db
def test_insert_on_pull_empty_table_to_populated(client, mock_scrape):
    """Test that POST /pull-data creates new rows in initially empty database."""
    assert AdmissionResult.count() == 0

    response = client.post("/grad-data/analysis")
    assert response.status_code == 200

    assert AdmissionResult.count() > 0

    # Fetch a single row and check it's not null
    row = AdmissionResult.execute_raw(f"SELECT * FROM {get_table()} LIMIT 1;", [])
    assert row is not None
    # Optionally check some fields
    assert row[0]["school"] is not None
    assert row[0]["program_name"] is not None


# b. Test idempotency / constraints
# i. Duplicate rows do not create duplicates in database (accidentally pulling the
# same data should not result in the database acquiring duplicated rows).


@pytest.mark.db
def test_idempotency_duplicate_rows_no_duplicates(client, mock_scrape):
    """Test that POST /pull-data creates new rows in initially empty database."""
    client.post("/grad-data/analysis")

    count = AdmissionResult.count()

    client.post("/grad-data/analysis")

    assert count == AdmissionResult.count()


# c. Test simple query function
# i. You should be able to query your data to return a dict with our expected keys
# (the required data fields within M3).


@pytest.mark.db
def test_simple_query_function_returns_expected_dict(client, mock_scrape):
    """Test that query functions return dictionaries with expected keys."""
    client.post("/grad-data/analysis")

    row = AdmissionResult.execute_raw(f"SELECT * FROM {get_table()} LIMIT 1;", [])[0]

    assert "school" in row
    assert "program_name" in row
    assert "gpa" in row
    assert "year" in row
    assert "status" in row
