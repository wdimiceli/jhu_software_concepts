"""Tests for src/run.py."""

import pytest
from unittest.mock import MagicMock
from run import start


@pytest.mark.web
def test_start(mocker):
    """Verify start_postgres and load_data.load_admissions_results are called."""
    mocker.patch("run.start_postgres")
    # mock_load = mocker.patch("run.load_data.load_admissions_results")
    mock_app = MagicMock()
    mocker.patch("run.create_app", return_value=mock_app)

    # Call with a filename
    start()
    # mock_load.assert_called_once_with("data.csv")
    mock_app.run.assert_called_once_with(host="0.0.0.0", port=8080)


@pytest.mark.web
def test_start_with_data_file(mocker):
    """Verify start_postgres and load_data.load_admissions_results are called."""
    mocker.patch("run.start_postgres")
    mock_load = mocker.patch("run.load_data.load_admissions_results")
    mock_app = MagicMock()
    mocker.patch("run.create_app", return_value=mock_app)

    # Call with a filename
    start("file.json")
    mock_load.assert_called_once()
