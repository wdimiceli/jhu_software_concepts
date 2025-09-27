"""Tests for the load_data module."""

import pytest
from load_data import load_admissions_results
from model import AdmissionResult


@pytest.mark.db
def test_load_admissions_results_success(empty_table):
    """Test successful loading of admissions results."""
    load_admissions_results("src/admissions_info.json")

    assert AdmissionResult.count() > 0


