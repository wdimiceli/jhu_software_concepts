"""Integration tests for end-to-end flows.

This module tests complete workflows from data pull through analysis update
to final rendering, ensuring the entire system works together correctly.
"""

import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup
import re
from model import AdmissionResult, get_table


# a. End-to-end (pull -> update -> Render)
# i. Inject a fake scraper that returns multiple records
# ii. POST /pull-data succeeds and rows are in DB
# iii. POST /update-analysis succeeds (when not busy)
# iv. GET /analysis shows updated analysis with correctly formatted values

@pytest.mark.integration
def test_end_to_end_pull_update_render(client, mock_scrape):
    """Test complete end-to-end flow: pull -> update -> render with correctly formatted values."""
    resp = client.get("/grad-data/analysis")
    page_text = resp.get_data(as_text=True)

    assert page_text.count("Percent accepted: N/A") > 0

    client.post("/grad-data/analysis")

    resp = client.get("/grad-data/analysis?refresh")
    page_text = resp.get_data(as_text=True)

    assert page_text.count("Percent accepted: N/A") == 0
    
    # # Must contain "Answer:" labels - should appear multiple times
    # answer_count = page_text.count("A:")
    # assert answer_count >= 1, "Page should contain at least one 'Answer:' label"

    # # Find all percentages in the response
    percentages = re.findall(r"\d+\.\d{2}%", page_text)
    
    # # Should find at least some percentages
    assert len(percentages) > 0, "Should find at least one percentage with two decimals"


# b. Multiple pulls
# i. Running POST /pull-data twice with overlapping data remains consistent with
# uniqueness policy.

@pytest.mark.integration
def test_multiple_pulls_idempotency(client, mock_scrape):
    """Test that running POST /analysis twice with overlapping data remains consistent."""
    client.post("/grad-data/analysis")

    # Fetch the first row and get its ID
    row = AdmissionResult.execute_raw(f"SELECT * FROM {get_table()} LIMIT 1;", [])[0]
    first_row_id = row["p_id"]

    client.post("/grad-data/analysis")

    # Check that there is exactly 1 row with that ID
    row_count_with_id = AdmissionResult.execute_raw(
        f"SELECT COUNT(*) AS count FROM {get_table()} WHERE p_id = %s;", [first_row_id]
    )
    assert row_count_with_id[0]["count"] == 1

#     fake_results = mock_scraper["fake_results"]
    
#     # Mock questions to avoid database calls
#     mock_questions = [{"prompt": "Test", "answer": 42, "formatted": "Answer: 42"}]
    
#     # Setup mock state and dependencies
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.threading.Thread'):
#             with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=100):
#                 with patch('blueprints.grad_data.routes.scrape.scrape_data', return_value=fake_results):
#                     with patch('blueprints.grad_data.routes.answer_questions', return_value=mock_questions):
#                         # Mock database operations
#                         for result in fake_results:
#                             result.clean_and_augment = MagicMock()
#                             result.save_to_db = MagicMock()
                        
#                         # First pull
#                         response1 = client.post("/grad-data/analysis")
#                         assert response1.status_code == 200
                        
#                         # Simulate completion of first pull
#                         from blueprints.grad_data.routes import begin_refresh
#                         with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=100):
#                             with patch('blueprints.grad_data.routes.scrape.scrape_data', return_value=fake_results):
#                                 begin_refresh()
                        
#                         # Reset mocks for second pull
#                         for result in fake_results:
#                             result.clean_and_augment.reset_mock()
#                             result.save_to_db.reset_mock()
                        
#                         # Second pull with same data
#                         response2 = client.post("/grad-data/analysis")
#                         assert response2.status_code == 200
                        
#                         # Simulate completion of second pull
#                         with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=100):
#                             with patch('blueprints.grad_data.routes.scrape.scrape_data', return_value=fake_results):
#                                 begin_refresh()
                        
#                         # Verify that save_to_db was called again (idempotency handled by DB constraints)
#                         for result in fake_results:
#                             result.save_to_db.assert_called_once()


# @pytest.mark.integration
# def test_pull_with_database_integration(client, mock_database):
#     """Test that pull operation correctly integrates with database."""
#     # Mock scraper results
#     fake_results = [
#         MagicMock(id=1, school="Test University", program_name="Computer Science"),
#         MagicMock(id=2, school="Elite Institute", program_name="Data Science")
#     ]
    
#     # Mock questions to avoid database calls
#     mock_questions = [{"prompt": "Test", "answer": 42, "formatted": "Answer: 42"}]
    
#     # Mock database to return initial count, then updated count
#     mock_database.fetchone.side_effect = [[0], [2]]  # Before: 0, After: 2
    
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.threading.Thread'):
#             with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=0):
#                 with patch('blueprints.grad_data.routes.scrape.scrape_data', return_value=fake_results):
#                     with patch('blueprints.grad_data.routes.answer_questions', return_value=mock_questions):
#                         # Setup result mocks
#                         for result in fake_results:
#                             result.clean_and_augment = MagicMock()
#                             result.save_to_db = MagicMock()
                        
#                         # Execute pull
#                         response = client.post("/grad-data/analysis")
#                         assert response.status_code == 200
                        
#                         # Simulate the background process completion
#                         from blueprints.grad_data.routes import begin_refresh
#                         with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=0):
#                             with patch('blueprints.grad_data.routes.scrape.scrape_data', return_value=fake_results):
#                                 begin_refresh()
                        
#                         # Verify processing occurred
#                         for result in fake_results:
#                             result.clean_and_augment.assert_called_once()
#                             result.save_to_db.assert_called_once()


# @pytest.mark.integration
# def test_error_handling_during_pull(client):
#     """Test system behavior when pull operation encounters errors."""
#     # Mock questions to avoid database calls
#     mock_questions = [{"prompt": "Test", "answer": 42, "formatted": "Answer: 42"}]
    
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.threading.Thread'):
#             with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=100):
#                 with patch('blueprints.grad_data.routes.answer_questions', return_value=mock_questions):
#                     # Simulate scraper error
#                     with patch('blueprints.grad_data.routes.scrape.scrape_data', side_effect=Exception("Scraping failed")):
                        
#                         # Should still return 200 (error handling in background)
#                         response = client.post("/grad-data/analysis")
#                         assert response.status_code == 200
                        
#                         # Test that begin_refresh handles the error gracefully
#                         from blueprints.grad_data.routes import begin_refresh
#                         with patch('blueprints.grad_data.routes.AdmissionResult.get_latest_id', return_value=100):
#                             with patch('blueprints.grad_data.routes.scrape.scrape_data', side_effect=Exception("Scraping failed")):
#                                 # Should not raise exception
#                                 begin_refresh()


# @pytest.mark.integration  
# def test_complete_workflow_with_formatting(client, mock_scraper):
#     """Test complete workflow ensures proper formatting in final output."""
#     # Use mock questions with various formatting scenarios
#     mock_questions = [
#         {
#             "prompt": "What percentage are international students?",
#             "answer": 23.456789,
#             "formatted": "International students: 23.46%"
#         },
#         {
#             "prompt": "What is the acceptance rate?", 
#             "answer": 67.1,
#             "formatted": "Acceptance rate: 67.10%"
#         },
#         {
#             "prompt": "Average GPA of accepted students?",
#             "answer": 3.789,
#             "formatted": "Average GPA: 3.79"
#         }
#     ]
    
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=mock_questions):
#             response = client.get("/grad-data/analysis")
#             assert response.status_code == 200
            
#             page_text = response.get_data(as_text=True)
            
#             # Verify percentages are formatted with exactly 2 decimals
#             percentages = re.findall(r"\d+\.\d{2}%", page_text)
#             assert len(percentages) >= 2
            
#             # Verify specific formatting
#             assert "23.46%" in page_text
#             assert "67.10%" in page_text
#             assert "3.79" in page_text
            
#             # Ensure no malformed percentages
#             malformed = re.findall(r"\d+\.(?:\d{1}|\d{3,})%", page_text) 
#             assert len(malformed) == 0


# @pytest.mark.integration
# def test_busy_state_integration(client):
#     """Test integration of busy state across the entire system."""
#     # Test when system is busy
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": True}):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#             response = client.get("/grad-data/analysis")
#             assert response.status_code == 200
            
#             soup = BeautifulSoup(response.data, "html.parser")
            
#             # Both buttons should be disabled
#             pull_button = soup.find(attrs={"data-testid": "pull-data-btn"})
#             update_button = soup.find(attrs={"data-testid": "update-analysis-btn"})
            
#             assert pull_button is not None
#             assert update_button is not None
#             assert pull_button.has_attr("disabled")
#             assert update_button.has_attr("disabled")
            
#             # Loader should be visible
#             loader = soup.find(class_="loader")
#             assert loader is not None
    
#     # Test when system is not busy
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.answer_questions', return_value=[]):
#             response = client.get("/grad-data/analysis")
#             assert response.status_code == 200
            
#             soup = BeautifulSoup(response.data, "html.parser")
            
#             # Buttons should not be disabled
#             pull_button = soup.find(attrs={"data-testid": "pull-data-btn"})
#             update_button = soup.find(attrs={"data-testid": "update-analysis-btn"})
            
#             assert pull_button is not None
#             assert update_button is not None
#             assert not pull_button.has_attr("disabled")
#             # Update button should not be disabled when not busy
#             assert not update_button.has_attr("disabled")
            
#             # No loader should be visible
#             loader = soup.find(class_="loader")
#             assert loader is None