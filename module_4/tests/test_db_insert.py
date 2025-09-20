"""Tests for database writes and query operations.

This module tests database insertion, idempotency constraints, and query
functions to ensure data integrity and proper schema compliance.
"""

import pytest
from unittest.mock import patch, MagicMock, call
from datetime import datetime
import os
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


# @pytest.mark.db
# def test_insert_required_fields(mock_scraper):
#     """Test that inserted rows contain all required (non-null) fields."""
#     fake_result = mock_scraper["fake_results"][0]
    
#     # Verify the result has required non-null fields (this is what the assignment actually asks for)
#     assert fake_result.id is not None
#     assert fake_result.school is not None
#     assert fake_result.program_name is not None
#     assert fake_result.decision_status is not None
    
#     # Test that save_to_db can be called without errors
#     fake_result.save_to_db = MagicMock()
#     fake_result.save_to_db()
#     fake_result.save_to_db.assert_called_once()


# @pytest.mark.db
# def test_idempotency_duplicate_rows_no_duplicates(mock_scraper):
#     """Test that duplicate pulls do not create duplicate rows in database."""
#     fake_result = mock_scraper["fake_results"][0]
    
#     # Mock save_to_db to simulate idempotent behavior
#     fake_result.save_to_db = MagicMock()
    
#     # First save
#     fake_result.save_to_db()
    
#     # Second save of same data (should handle duplicates via constraints)
#     fake_result.save_to_db()
    
#     # Verify save_to_db was called twice but would handle duplicates properly
#     assert fake_result.save_to_db.call_count == 2
    
#     # The actual idempotency is handled by the database ON CONFLICT clause
#     # which we've verified exists in the model.py save_to_db method


# @pytest.mark.db
# def test_constraints_prevent_duplicates():
#     """Test that database constraints prevent duplicate entries."""
#     # Create two identical admission results
#     result1 = AdmissionResult(
#         id=12345,
#         school="Test University",
#         program_name="Computer Science",
#         degree_type="masters",
#         added_on=datetime(2024, 1, 1),
#         decision_status="accepted",
#         decision_date=datetime(2024, 2, 1),
#         season="fall",
#         year=2025,
#         applicant_region="american",
#         gre_general=320,
#         gre_verbal=160,
#         gre_analytical_writing=4.5,
#         gpa=3.8,
#         comments="Great program!",
#         full_info_url="/result/12345",
#         llm_generated_program=None,
#         llm_generated_university=None
#     )
    
#     result2 = AdmissionResult(
#         id=12345,  # Same ID - should trigger constraint
#         school="Different University",
#         program_name="Different Program",
#         degree_type="phd",
#         added_on=datetime(2024, 1, 2),
#         decision_status="rejected",
#         decision_date=datetime(2024, 2, 2),
#         season="spring",
#         year=2024,
#         applicant_region="international",
#         gre_general=315,
#         gre_verbal=155,
#         gre_analytical_writing=4.0,
#         gpa=3.7,
#         comments="Different program!",
#         full_info_url="/result/12345",
#         llm_generated_program=None,
#         llm_generated_university=None
#     )
    
#     with patch('model.get_connection') as mock_conn:
#         mock_cursor = MagicMock()
#         mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
#         # Save first result
#         result1.save_to_db()
        
#         # Save second result with same ID - should update, not duplicate
#         result2.save_to_db()
        
#         # Verify both saves used the ON CONFLICT clause
#         assert mock_cursor.execute.call_count == 2
#         for call_instance in mock_cursor.execute.call_args_list:
#             sql_query = call_instance[0][0]
#             assert "ON CONFLICT (p_id) DO UPDATE SET" in sql_query


# @pytest.mark.db
# def test_simple_query_function_returns_expected_dict():
#     """Test that query functions return dictionaries with expected keys."""
#     # Test AdmissionResult.execute_raw method
#     expected_result = [
#         {
#             "count": 150,
#             "avg_gpa": 3.45,
#             "avg_gre": 315.2,
#             "pct": 25.5,
#             "school": "Test University",
#             "program_name": "Computer Science",
#             "status": "accepted"
#         }
#     ]
    
#     with patch('model.get_connection') as mock_conn:
#         mock_cursor = MagicMock()
#         mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
#         mock_cursor.execute.return_value.fetchall.return_value = expected_result
        
#         # Test execute_raw method
#         result = AdmissionResult.execute_raw(
#             "SELECT COUNT(*) as count FROM admissions_info WHERE year=%s",
#             [2025]
#         )
        
#         # Verify it returns the expected dictionary structure
#         assert isinstance(result, list)
#         assert len(result) == 1
#         assert isinstance(result[0], dict)
        
#         # Verify expected keys are present
#         expected_keys = ["count", "avg_gpa", "avg_gre", "pct", "school", "program_name", "status"]
#         for key in expected_keys:
#             assert key in result[0]


# @pytest.mark.db
# def test_query_data_returns_required_fields():
#     """Test that query_data functions return dictionaries with Module-3 required fields."""
#     from query_data import answer_questions
    
#     # Mock database responses for all queries
#     mock_responses = [
#         [{"count": 150}],  # Fall 2025 count
#         [{"pct": 25.5}],   # International percentage  
#         [{"avg_gpa": 3.45, "avg_gre": 315.2, "avg_gre_v": 160.1, "avg_gre_aw": 4.2}],  # Averages
#         [{"avg_gpa": 3.67}],  # American Fall 2025 GPA
#         [{"pct": 45.8}],      # Fall 2025 acceptance rate
#         [{"avg_gpa": 3.78}],  # Accepted Fall 2025 GPA
#         [{"count": 25}],      # JHU CS masters count
#         [{"count": 8}],       # Georgetown PhD acceptances
#         [{"avg_gpa_ucla": 3.85, "avg_gpa_usc": 3.72}],  # UCLA vs USC
#         [{"avg_gre_2021": 310.5, "avg_gre_2022": 312.1, "avg_gre_2023": 314.2, "avg_gre_2024": 316.8}]  # 4-year GRE
#     ]
    
#     with patch('query_data.AdmissionResult.execute_raw') as mock_execute_raw:
#         mock_execute_raw.side_effect = mock_responses
        
#         questions = answer_questions()
        
#         # Verify return structure has required keys
#         assert isinstance(questions, list)
#         assert len(questions) > 0
        
#         for question in questions:
#             # Each question should be a dict with required Module-3 fields
#             assert isinstance(question, dict)
#             assert "prompt" in question
#             assert "answer" in question  
#             assert "formatted" in question
            
#             # Verify types
#             assert isinstance(question["prompt"], str)
#             assert question["answer"] is not None
#             assert isinstance(question["formatted"], str)


# @pytest.mark.db
# def test_database_connection_and_table_initialization():
#     """Test database table initialization with required schema."""
#     with patch('model.get_connection') as mock_conn:
#         mock_cursor = MagicMock()
#         mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        
#         # Test table initialization
#         init_tables(recreate=False)
        
#         # Verify CREATE TABLE was called
#         mock_cursor.execute.assert_called()
#         sql_calls = [call_args[0][0] for call_args in mock_cursor.execute.call_args_list]
        
#         # Find the CREATE TABLE statement
#         create_table_sql = None
#         for sql in sql_calls:
#             if "CREATE TABLE IF NOT EXISTS admissions_info" in sql:
#                 create_table_sql = sql
#                 break
        
#         assert create_table_sql is not None
        
#         # Verify required schema fields are present
#         required_fields = [
#             "p_id INTEGER PRIMARY KEY",
#             "school TEXT",
#             "program_name TEXT", 
#             "status TEXT",
#             "season TEXT",
#             "year INTEGER",
#             "us_or_international TEXT",
#             "gpa FLOAT",
#             "gre FLOAT"
#         ]
        
#         for field in required_fields:
#             assert field in create_table_sql or field.replace("FLOAT", "REAL") in create_table_sql


# @pytest.mark.db
# def test_admission_result_count_method():
#     """Test AdmissionResult.count() method functionality."""
#     with patch('model.get_connection') as mock_conn:
#         mock_cursor = MagicMock() 
#         mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
#         mock_cursor.fetchone.return_value = [42]
        
#         # Test count with no where clause
#         count = AdmissionResult.count()
#         assert count == 42
        
#         # Verify SQL was executed
#         mock_cursor.execute.assert_called_once()
#         sql_query = mock_cursor.execute.call_args[0][0]
#         assert "SELECT COUNT(*) from admissions_info" in sql_query
        
#         # Test count with where clause
#         mock_cursor.reset_mock()
#         mock_cursor.fetchone.return_value = [15]
        
#         count_filtered = AdmissionResult.count({"year": 2025, "season": "fall"})
#         assert count_filtered == 15
        
#         # Verify WHERE clause was added
#         sql_query = mock_cursor.execute.call_args[0][0]
#         assert "WHERE" in sql_query
#         assert "year=%s" in sql_query
#         assert "season=%s" in sql_query


# @pytest.mark.db
# def test_get_latest_id_method():
#     """Test AdmissionResult.get_latest_id() method."""
#     from model import AdmissionResult
    
#     # Mock AdmissionResult.get_latest_id directly for consistent behavior
#     with patch.object(AdmissionResult, 'get_latest_id') as mock_get_latest:
#         # Test with existing data
#         mock_get_latest.return_value = 12345
#         latest_id = AdmissionResult.get_latest_id()
#         assert latest_id == 12345
        
#         # Test with empty table
#         mock_get_latest.return_value = 0
#         latest_id = AdmissionResult.get_latest_id()
#         assert latest_id == 0
        
#         # Verify it was called
#         assert mock_get_latest.call_count == 2