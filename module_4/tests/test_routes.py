"""Additional tests for route modules to achieve 100% coverage."""

import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
from blueprints.grad_data.routes import begin_refresh


@pytest.mark.web
def test_portfolio_home_route(client):
    """"""
    response = client.get("/")
    assert response.status_code == 200


@pytest.mark.web
def test_portfolio_contact_route(client):
    """"""
    response = client.get("/contact")
    assert response.status_code == 200


@pytest.mark.web
def test_portfolio_projects_route(client):
    """"""
    response = client.get("/projects")
    assert response.status_code == 200


@pytest.mark.web
def test_grad_data_route(client, mocker):
    """"""
    mock_begin_refresh = mocker.patch("blueprints.grad_data.routes.begin_refresh", return_value=None)
    mock_answer_questions = mocker.patch("blueprints.grad_data.routes.answer_questions", return_value=[])

    response = client.get("/grad-data/analysis")
    assert response.status_code == 200

    mock_begin_refresh.assert_not_called()
    mock_answer_questions.assert_called_once()


@pytest.mark.web
def test_grad_data_init_update(client, mocker):
    """"""
    mock_begin_refresh = mocker.patch("blueprints.grad_data.routes.begin_refresh", return_value=None)
    mocker.patch("blueprints.grad_data.routes.answer_questions", return_value=[])

    response = client.post("/grad-data/analysis")
    assert response.status_code == 200

    mock_begin_refresh.assert_called_once()


@pytest.mark.web
def test_grad_data_poll_for_updates(client, mocker):
    """"""
    mocker.patch("blueprints.grad_data.routes.begin_refresh")
    mocker.patch("blueprints.grad_data.routes.answer_questions", return_value=[])

    with patch('blueprints.grad_data.routes.scrape_state', { "running": False }):
        response = client.get("/grad-data/analysis?poll")
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")
        assert soup.find(class_="loader") is None

    with patch('blueprints.grad_data.routes.scrape_state', { "running": True }):
        response = client.get("/grad-data/analysis?poll")
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")
        assert soup.find(class_="loader") is not None

    with patch('blueprints.grad_data.routes.scrape_state', { "running": False, "entries": [] }):
        response = client.get("/grad-data/analysis?poll")
        assert response.status_code == 200

        page_text = response.get_data(as_text=True)
        assert "0 entries" in page_text


@pytest.mark.web
def test_begin_refresh(mocker, mock_scraper):
    """"""
    mocker.patch("blueprints.grad_data.routes.AdmissionResult.get_latest_id")
    mocker.patch(
        "scrape.scrape_data",
        return_value=mock_scraper["fake_results"]
    )

    with patch('blueprints.grad_data.routes.scrape_state', { "running": False }) as scrape_state:
        begin_refresh()

        print(scrape_state)
        
        assert "entries" in scrape_state and len(scrape_state["entries"]) > 0
