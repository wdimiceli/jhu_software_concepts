"""Tests for button endpoints and busy-state behavior."""

import pytest
from unittest.mock import patch


# Test POST /pull-data (or whatever you named the path posting the pull data request)
# i. Returns 200
# ii. Triggers the loader with the rows from the scraper (should be faked / mocked)


@pytest.mark.buttons
def test_post_pull_data_returns_200_and_triggers_loader(client, mocker, mock_scrape):
    """Ensure POST /grad-data/analysis returns 200 and triggers the loader when not busy."""
    mocker.patch("model.AdmissionResult.get_latest_id", return_value=100)

    with patch("blueprints.grad_data.routes.scrape_state", {"running": False}):
        response = client.post("/grad-data/analysis")
        assert response.status_code == 200


# b. Test POST /update-analysis (or whatever you named the path posting the update analysis
# request)
# i. Returns 200 when not busy


@pytest.mark.buttons
def test_get_update_analysis_returns_200_when_not_busy(client, empty_table):
    """Ensure GET /grad-data/analysis?refresh returns 200 when not busy."""
    with patch("blueprints.grad_data.routes.scrape_state", {"running": False}):
        response = client.get("/grad-data/analysis?refresh")
        assert response.status_code == 200


# c. Test busy gating
# i. When a pull is “in progress”, POST /update-analysis returns 409 (and performs
# no update).
# ii. When busy, POST /pull-data returns 409


@pytest.mark.buttons
def test_busy_gating_pull_data_button_disabled(client, mock_scrape):
    """Ensure POST /grad-data/analysis returns 409 when a pull is already running."""
    with patch("blueprints.grad_data.routes.scrape_state", {"running": True}):
        response = client.post("/grad-data/analysis")
        assert response.status_code == 409


@pytest.mark.buttons
def test_busy_gating_update_analysis_button_disabled(client, empty_table):
    """Ensure GET /grad-data/analysis?refresh returns 409 when a pull is already running."""
    with patch("blueprints.grad_data.routes.scrape_state", {"running": True}):
        response = client.get("/grad-data/analysis?refresh")
        assert response.status_code == 409
