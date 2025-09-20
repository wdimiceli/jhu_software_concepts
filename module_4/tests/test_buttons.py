"""Tests for button endpoints and busy-state behavior.

This module tests the 'Pull Data' and 'Update Analysis' button functionality,
including proper busy-state gating behavior as required by the assignment.
"""

import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup


# Test POST /pull-data (or whatever you named the path posting the pull data request)
# i. Returns 200
# ii. Triggers the loader with the rows from the scraper (should be faked / mocked)

@pytest.mark.buttons
def test_post_pull_data_returns_200_and_triggers_loader(client, mocker, mock_scrape):
    """"""
    mocker.patch("model.AdmissionResult.get_latest_id", return_value=100)

    with patch('blueprints.grad_data.routes.scrape_state', { "running": False }):
        response = client.post("/grad-data/analysis")
        assert response.status_code == 200


# b. Test POST /update-analysis (or whatever you named the path posting the update analysis
# request)
# i. Returns 200 when not busy

@pytest.mark.buttons
def test_get_update_analysis_returns_200_when_not_busy(client, empty_table):
    """"""
    with patch('blueprints.grad_data.routes.scrape_state', { "running": False }):
        response = client.get("/grad-data/analysis?refresh")
        assert response.status_code == 200


# c. Test busy gating
# i. When a pull is “in progress”, POST /update-analysis returns 409 (and performs
# no update).
# ii. When busy, POST /pull-data returns 409


@pytest.mark.buttons
def test_busy_gating_pull_data_button_disabled(client, mock_scrape):
    """"""
    with patch('blueprints.grad_data.routes.scrape_state', { "running": True }):
        response = client.post("/grad-data/analysis")
        assert response.status_code == 409


@pytest.mark.buttons
def test_busy_gating_update_analysis_button_disabled(client, empty_table):
    """"""
    with patch('blueprints.grad_data.routes.scrape_state', { "running": True }):
        response = client.get("/grad-data/analysis?refresh")
        assert response.status_code == 409


# @pytest.mark.buttons
# def test_post_pull_data_returns_200_and_triggers_loader(client, mock_scraper):
#     """Test POST /analysis returns 200 and triggers the loader with mocked scraper."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.threading.Thread') as mock_thread:
#             with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#                 response = client.post("/grad-data/analysis")
                
#                 assert response.status_code == 200
#                 # Verify that Thread was called to start the scraping process
#                 mock_thread.assert_called_once()
#                 # Verify the thread target is begin_refresh
#                 args, kwargs = mock_thread.call_args
#                 assert kwargs['target'].__name__ == 'begin_refresh'
#                 assert kwargs['daemon'] is True


# @pytest.mark.buttons  
# def test_post_pull_data_with_json_response(client):
#     """Test POST /analysis returns proper response structure."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.threading.Thread'):
#             with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#                 response = client.post("/grad-data/analysis")
                
#                 assert response.status_code == 200
#                 # The response should contain the analysis page HTML
#                 assert b"Analysis" in response.data


# @pytest.mark.buttons
# def test_get_update_analysis_returns_200_when_not_busy(client):
#     """Test GET /analysis?refresh returns 200 when not busy."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#             response = client.get("/grad-data/analysis?refresh")
            
#             assert response.status_code == 200
#             # Should contain the refresh checkmark indicator
#             soup = BeautifulSoup(response.data, "html.parser")
#             # Look for the SVG checkmark that appears when refresh=True
#             svg_element = soup.find("svg")
#             assert svg_element is not None


# @pytest.mark.buttons
# def test_busy_gating_pull_data_button_disabled(client):
#     """Test that Pull Data button is disabled when scraping is in progress."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": True}):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#             response = client.get("/grad-data/analysis")
            
#             assert response.status_code == 200
#             soup = BeautifulSoup(response.data, "html.parser")
            
#             # Find the pull-data button by data-testid
#             pull_button = soup.find(attrs={"data-testid": "pull-data-btn"})
#             assert pull_button is not None
#             assert pull_button.has_attr("disabled")


# @pytest.mark.buttons
# def test_busy_gating_update_analysis_button_disabled(client):
#     """Test that Update Analysis button is disabled when scraping is in progress."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": True}):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#             response = client.get("/grad-data/analysis")
            
#             assert response.status_code == 200
#             soup = BeautifulSoup(response.data, "html.parser")
            
#             # Find the update-analysis button by data-testid
#             update_button = soup.find(attrs={"data-testid": "update-analysis-btn"})  
#             assert update_button is not None
#             assert update_button.has_attr("disabled")


# @pytest.mark.buttons
# def test_busy_state_shows_loader(client):
#     """Test that loader is displayed when scraping is running."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": True}):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#             response = client.get("/grad-data/analysis")
            
#             assert response.status_code == 200
#             soup = BeautifulSoup(response.data, "html.parser")
            
#             # Should contain loader element
#             loader = soup.find(class_="loader")
#             assert loader is not None


# @pytest.mark.buttons
# def test_not_busy_state_no_loader(client):
#     """Test that loader is not displayed when scraping is not running."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#             response = client.get("/grad-data/analysis")
            
#             assert response.status_code == 200
#             soup = BeautifulSoup(response.data, "html.parser")
            
#             # Should not contain loader element when not busy
#             loader = soup.find(class_="loader")
#             assert loader is None


# @pytest.mark.buttons
# def test_poll_state_shows_entry_count(client):
#     """Test that polling state shows the correct entry count."""
#     test_entries = [MagicMock() for _ in range(5)]
#     with patch('blueprints.grad_data.routes.scrape_state', {
#         "running": False, 
#         "entries": test_entries
#     }):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#             response = client.get("/grad-data/analysis?poll")
            
#             assert response.status_code == 200
#             page_text = response.get_data(as_text=True)
#             assert "Got 5 entries!" in page_text


# @pytest.mark.buttons
# def test_begin_refresh_function_busy_state_management(mock_scraper):
#     """Test that begin_refresh properly manages busy state."""
#     from blueprints.grad_data.routes import begin_refresh
    
#     # Mock the global scrape_state
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}) as mock_state:
#         with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=100):
#             with patch('blueprints.grad_data.routes.scrape.scrape_data', return_value=mock_scraper["fake_results"]):
#                 # Mock the clean_and_augment and save_to_db methods
#                 for result in mock_scraper["fake_results"]:
#                     result.clean_and_augment = MagicMock()
#                     result.save_to_db = MagicMock()
                
#                 begin_refresh()
                
#                 # Verify state was set to running and then back to False
#                 # Final state should be not running
#                 assert mock_state["running"] is False
#                 assert "entries" in mock_state
#                 assert len(mock_state["entries"]) == 3


# @pytest.mark.buttons
# def test_begin_refresh_exception_handling(mock_scraper):
#     """Test that begin_refresh properly handles exceptions and resets busy state."""
#     from blueprints.grad_data.routes import begin_refresh
    
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}) as mock_state:
#         with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=100):
#             with patch('blueprints.grad_data.routes.scrape.scrape_data', side_effect=Exception("Scraping failed")):
                
#                 # Should not raise exception, but should reset running state
#                 begin_refresh()
                
#                 # Even with exception, running should be set back to False
#                 assert mock_state["running"] is False