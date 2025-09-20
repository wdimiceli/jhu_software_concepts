"""Tests for Flask app factory, configuration, and page rendering.

This module tests the core Flask application setup, route configuration,
and the GET /analysis page rendering as required by the assignment.
"""

import pytest
from bs4 import BeautifulSoup


# a. Test app factory / Config: Assert a testable Flask app is created with required routes (e.g.
# should test each of your “/routes” that you establish in flask).


@pytest.mark.web
def test_app_factory_config_creates_testable_app(app):
    """Test app factory creates a testable Flask app with required routes."""
    assert app is not None

    # Check that required blueprints are registered
    blueprint_names = [bp.name for bp in app.blueprints.values()]
    assert "portfolio" in blueprint_names
    assert "grad_data" in blueprint_names


@pytest.mark.web
def test_required_routes_registered(app):
    """Test that all required routes are properly registered in the Flask app."""
    # Get all registered routes
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append(rule.rule)

    # Verify required routes exist
    required_routes = [
        "/",  # Portfolio home
        "/contact",  # Portfolio contact
        "/projects",  # Portfolio projects
        "/grad-data/analysis",  # Analysis page
    ]

    for route in required_routes:
        assert route in routes, f"Required route {route} not found in registered routes"


@pytest.mark.web
def test_portfolio_home_route(client):
    """Test that the home route ("/") of the portfolio is accessible."""
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.web
def test_portfolio_contact_route(client):
    """Test that the contact route ("/contact") of the portfolio is accessible."""
    response = client.get("/contact")
    assert response.status_code == 200


@pytest.mark.web
def test_portfolio_projects_route(client):
    """Test that the projects route ("/projects") of the portfolio is accessible."""
    response = client.get("/projects")
    assert response.status_code == 200


# b. Test GET /analysis (page load)
# i. Status 200.
# ii. Page Contains both “Pull Data” and “Update Analysis” buttons
# iii. Page text includes “Analysis” and at least one “Answer:”


@pytest.mark.web
def test_grad_data_route(client, mocker, mock_answer_questions, empty_table):
    """Test that the graduate data analysis route ("/grad-data/analysis") is accessible."""
    mock_begin_refresh = mocker.patch(
        "blueprints.grad_data.routes.begin_refresh", return_value=None
    )
    mock_answer_questions = mocker.patch(
        "blueprints.grad_data.routes.answer_questions", return_value=mock_answer_questions
    )

    response = client.get("/grad-data/analysis")
    assert response.status_code == 200

    mock_begin_refresh.assert_not_called()
    mock_answer_questions.assert_called_once()

    soup = BeautifulSoup(response.data, "html.parser")

    # Test page contains both required buttons with correct data-testid
    pull_button = soup.find(attrs={"data-testid": "pull-data-btn"})
    update_button = soup.find(attrs={"data-testid": "update-analysis-btn"})

    assert pull_button is not None, "Pull Data button not found"
    assert update_button is not None, "Update Analysis button not found"
    assert "Pull Data" in pull_button.get_text()
    assert "Update Analysis" in update_button.get_text()

    # Test page contains at least one "Answer:" label
    page_text = response.get_data(as_text=True)
    answer_count = page_text.count("A:")
    assert answer_count >= 1, "Page should contain at least one 'Answer:' label"
