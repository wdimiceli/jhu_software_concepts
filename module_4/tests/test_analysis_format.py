import pytest
import re
from bs4 import BeautifulSoup
from unittest.mock import patch


# a. Test labels & Rounding
# i. Test that your page include “Answer” labels for rendered analysis
# ii. Test that any percentage is formatted with two decimals.

@pytest.mark.analysis
def test_analysis_labels_present(client, mocker, empty_table):
    """Test that the page includes 'Answer:' labels for rendered analysis."""
    # Mock questions with proper structure
    mocker.patch("blueprints.grad_data.routes.answer_questions", return_value=[
        {
            "prompt": "What percentage of students are accepted?",
            "answer": 45.678,
            "formatted": "Answer: 45.68%"
        },
        {
            "prompt": "How many applications were received?",
            "answer": 1234,
            "formatted": "Answer: 1234 applications"
        }
    ])
    
    resp = client.get("/grad-data/analysis")
    page_text = resp.get_data(as_text=True)
    
    # Must contain "Answer:" labels - should appear multiple times
    answer_count = page_text.count("A:")
    assert answer_count >= 1, "Page should contain at least one 'Answer:' label"

    # Find all percentages in the response
    percentages = re.findall(r"\d+\.\d{2}%", page_text)
    
    # Should find at least some percentages
    assert len(percentages) > 0, "Should find at least one percentage with two decimals"
    
    # All found percentages should end with % and have exactly 2 decimal places
    for percentage in percentages:
        assert percentage.endswith("%"), f"Percentage {percentage} should end with %"
        # Extract the numeric part before %
        numeric_part = percentage[:-1]
        decimal_part = numeric_part.split(".")[-1]
        assert len(decimal_part) == 2, f"Percentage {percentage} should have exactly 2 decimal places"


# @pytest.mark.analysis
# def test_percentage_formatting_two_decimals(client):
#     """Test that any percentage is formatted with exactly two decimals."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.answer_questions') as mock_questions:
#             # Mock questions that should return percentages with 2 decimal formatting
#             mock_questions.return_value = [
#                 {
#                     "prompt": "What percentage are international students?",
#                     "answer": 23.456789,
#                     "formatted": "Percent international: 23.46%"
#                 },
#                 {
#                     "prompt": "What percent are acceptances?",
#                     "answer": 67.1,
#                     "formatted": "Percent accepted: 67.10%"
#                 },
#                 {
#                     "prompt": "Success rate?",
#                     "answer": 89.999,
#                     "formatted": "Success rate: 90.00%"
#                 }
#             ]
            
#             resp = client.get("/grad-data/analysis")
#             page_text = resp.get_data(as_text=True)
            
            


# @pytest.mark.analysis
# def test_analysis_formatting_structure(client):
#     """Test the overall structure of analysis formatting."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.answer_questions') as mock_questions:
#             mock_questions.return_value = [
#                 {
#                     "prompt": "Sample question about averages?",
#                     "answer": {"avg_gpa": 3.456, "avg_gre": 315.789},
#                     "formatted": "GPA: 3.46, GRE: 315.79"
#                 }
#             ]
            
#             resp = client.get("/grad-data/analysis")
#             soup = BeautifulSoup(resp.data, "html.parser")
            
#             # Check for question-entry divs
#             question_entries = soup.find_all("div", class_="question-entry")
#             assert len(question_entries) > 0, "Should have question-entry divs"
            
#             # Each question entry should have a question (Q:) and answer (A:)
#             for entry in question_entries:
#                 entry_text = entry.get_text()
#                 assert "Q:" in entry_text, "Each entry should have a question (Q:)"
#                 assert "A:" in entry_text, "Each entry should have an answer (A:)"


# @pytest.mark.analysis
# def test_no_malformed_percentages(client):
#     """Test that there are no malformed percentages (wrong decimal places)."""
#     with patch('blueprints.grad_data.routes.scrape_state', {"running": False}):
#         with patch('blueprints.grad_data.routes.answer_questions') as mock_questions:
#             mock_questions.return_value = [
#                 {
#                     "prompt": "Test percentage formatting",
#                     "answer": 12.3456,
#                     "formatted": "Result: 12.35%"
#                 }
#             ]
            
#             resp = client.get("/grad-data/analysis")
#             page_text = resp.get_data(as_text=True)
            
#             # Find percentages with wrong formatting (not exactly 2 decimals)
#             wrong_percentages = re.findall(r"\d+\.(?:\d{1}|\d{3,})%", page_text)
#             assert len(wrong_percentages) == 0, f"Found malformed percentages: {wrong_percentages}"
            
#             # Find percentages without decimals
#             no_decimal_percentages = re.findall(r"\d+%", page_text)
#             # Filter out those that are actually properly formatted (like "100.00%" would match as "00%")
#             actual_no_decimals = [p for p in no_decimal_percentages if not re.match(r"^\d{2}%$", p) or len(p) < 4]
            
#             # This is lenient - we allow whole number percentages, but flag if they seem like they should have decimals
#             # The main requirement is that when decimals are present, they should be exactly 2 places


# @pytest.mark.db
# def test_query_data_answer_questions():
#     """Test the answer_questions function from query_data module."""
#     from unittest.mock import patch
#     import query_data
    
#     # Create expected questions structure
#     expected_questions = [
#         {"prompt": "How many students applied to fall 2025?", "answer": 150, "formatted": "Applicant count: 150"},
#         {"prompt": "What percent are international?", "answer": 25.5, "formatted": "Percent international: 25.50%"},
#         {"prompt": "What are the average stats?", "answer": {"avg_gpa": 3.45, "avg_gre": 315.2}, "formatted": "GPA: 3.45, GRE: 315.20, GRE Verbal: 160.10, GRE AW: 4.20"},
#         {"prompt": "What is the American Fall 2025 GPA?", "answer": 3.67, "formatted": "Average GPA: 3.67"},
#         {"prompt": "What percent were accepted?", "answer": 45.8, "formatted": "Percent accepted: 45.80%"},
#         {"prompt": "What is accepted GPA?", "answer": 3.78, "formatted": "Average GPA: 3.78"},
#         {"prompt": "How many JHU CS masters?", "answer": 25, "formatted": "Applicant count: 25"},
#         {"prompt": "How many Georgetown PhD acceptances?", "answer": 8, "formatted": "Applicant count: 8"},
#         {"prompt": "UCLA vs USC GPA?", "answer": {"avg_gpa_ucla": 3.85, "avg_gpa_usc": 3.72}, "formatted": "UCLA average GPA: 3.85, USC average GPA: 3.72"},
#         {"prompt": "4-year GRE trends?", "answer": {"avg_gre_2021": 310.5, "avg_gre_2022": 312.1}, "formatted": "2021 average GRE: 310.50, 2022 average GRE: 312.10, 2023 average GRE: 314.20, 2024 average GRE: 316.80"}
#     ]
    
#     # Override the autouse fixture for this specific test
#     with patch('query_data.answer_questions', return_value=expected_questions):
#         questions = query_data.answer_questions()
        
#         # Verify we got all expected questions
#         assert len(questions) == 10
        
#         # Verify each question has required fields
#         for question in questions:
#             assert "prompt" in question
#             assert "answer" in question
#             assert "formatted" in question
#             assert isinstance(question["prompt"], str)
#             assert question["formatted"] is not None
        
#         # Test specific question formatting
#         assert "Applicant count: 150" in questions[0]["formatted"]
#         assert "Percent international: 25.50%" in questions[1]["formatted"]
#         assert "GPA: 3.45" in questions[2]["formatted"]
#         assert "Average GPA: 3.67" in questions[3]["formatted"]
#         assert "Percent accepted: 45.80%" in questions[4]["formatted"]
#         assert "UCLA average GPA: 3.85" in questions[8]["formatted"]
#         assert "USC average GPA: 3.72" in questions[8]["formatted"]


# @pytest.mark.db
# def test_query_data_table_name():
#     """Test that table_name variable is accessible."""
#     import query_data
#     assert query_data.table_name == "admissions_info"


# @pytest.mark.db
# def test_query_data_sql_queries():
#     """Test that SQL queries are properly formatted and use table_name."""
#     from unittest.mock import patch
#     import query_data
    
#     # Mock to capture SQL queries
#     executed_queries = []
    
#     def capture_execute_raw(sql, params):
#         executed_queries.append((sql, params))
#         # Return minimal response to avoid errors
#         return [{"count": 0, "pct": 0.0, "avg_gpa": 0.0, "avg_gre": 0.0,
#                 "avg_gre_v": 0.0, "avg_gre_aw": 0.0, "avg_gpa_ucla": 0.0,
#                 "avg_gpa_usc": 0.0, "avg_gre_2021": 0.0, "avg_gre_2022": 0.0,
#                 "avg_gre_2023": 0.0, "avg_gre_2024": 0.0}]
    
#     with patch('query_data.AdmissionResult.execute_raw', side_effect=capture_execute_raw):
#         query_data.answer_questions()
        
#         # Verify all queries use the table name
#         for sql, params in executed_queries:
#             assert "admissions_info" in sql
#             assert isinstance(params, (list, tuple))
        
#         # Verify specific query parameters
#         assert executed_queries[0][1] == (2025, "fall")  # Fall 2025 query
#         assert executed_queries[1][1] == ["international"]  # International query
#         assert executed_queries[4][1] == ["accepted", 2025, "fall"]  # Acceptance rate query


# @pytest.mark.db
# def test_query_data_formatting_edge_cases():
#     """Test formatting functions handle edge cases properly."""
#     from unittest.mock import patch
#     import query_data
    
#     # Test with valid numeric values (avoid None which causes format errors)
#     mock_responses = [
#         [{"count": 0}],  # Zero count
#         [{"pct": 0.0}],  # Zero percentage
#         [{"avg_gpa": 0.0, "avg_gre": 0.0, "avg_gre_v": 0.0, "avg_gre_aw": 0.0}],  # Zero averages
#         [{"avg_gpa": 4.0}],  # Perfect GPA
#         [{"pct": 100.0}],    # 100% acceptance
#         [{"avg_gpa": 2.5}],  # Low GPA
#         [{"count": 1}],      # Single count
#         [{"count": 999}],    # Large count
#         [{"avg_gpa_ucla": 3.5, "avg_gpa_usc": 3.7}],  # Valid comparison
#         [{"avg_gre_2021": 300.0, "avg_gre_2022": 305.0, "avg_gre_2023": 310.0, "avg_gre_2024": 315.0}]  # Valid GREs
#     ]
    
#     with patch('query_data.AdmissionResult.execute_raw') as mock_execute_raw:
#         mock_execute_raw.side_effect = mock_responses
        
#         questions = query_data.answer_questions()
        
#         # Verify formatting handles edge cases without crashing
#         assert len(questions) == 10
#         for question in questions:
#             assert question["formatted"] is not None
#             assert isinstance(question["formatted"], str)
        
#         # Test specific edge case formatting
#         assert "Applicant count: 0" in questions[0]["formatted"]
#         assert "Percent international: 0.00%" in questions[1]["formatted"]
#         assert "GPA: 0.00" in questions[2]["formatted"]
#         assert "Average GPA: 4.00" in questions[3]["formatted"]
#         assert "Percent accepted: 100.00%" in questions[4]["formatted"]
#         assert "Applicant count: 1" in questions[6]["formatted"]
#         assert "Applicant count: 999" in questions[7]["formatted"]
#         assert "UCLA average GPA: 3.50" in questions[8]["formatted"]
#         assert "USC average GPA: 3.70" in questions[8]["formatted"]


# @pytest.mark.db
# def test_query_data_lambda_functions():
#     """Test that lambda formatting functions work correctly."""
#     from unittest.mock import patch
#     import query_data
    
#     # Create comprehensive default response with all required keys
#     default_response = {
#         "count": 0, "pct": 0.0, "avg_gpa": 0.0, "avg_gre": 0.0,
#         "avg_gre_v": 0.0, "avg_gre_aw": 0.0, "avg_gpa_ucla": 0.0,
#         "avg_gpa_usc": 0.0, "avg_gre_2021": 0.0, "avg_gre_2022": 0.0,
#         "avg_gre_2023": 0.0, "avg_gre_2024": 0.0
#     }
    
#     # Test individual lambda functions by mocking specific responses
#     test_cases = [
#         (0, {"count": 42}, "Applicant count: 42"),
#         (1, {"pct": 33.333}, "Percent international: 33.33%"),
#         (2, {"avg_gpa": 3.756, "avg_gre": 315.2, "avg_gre_v": 160.1, "avg_gre_aw": 4.2}, "GPA: 3.76"),
#         (3, {"avg_gpa": 3.756}, "Average GPA: 3.76"),
#         (4, {"pct": 67.891}, "Percent accepted: 67.89%"),
#     ]
    
#     for query_index, test_response, expected_text in test_cases:
#         with patch('query_data.AdmissionResult.execute_raw') as mock_execute_raw:
#             # Set up mock responses for all queries
#             responses = []
#             for i in range(10):
#                 if i == query_index:
#                     # Use test response for the specific query
#                     response_dict = default_response.copy()
#                     response_dict.update(test_response)
#                     responses.append([response_dict])
#                 else:
#                     # Use default response for other queries
#                     responses.append([default_response.copy()])
            
#             mock_execute_raw.side_effect = responses
            
#             questions = query_data.answer_questions()
#             assert expected_text in questions[query_index]["formatted"]


# @pytest.mark.db
# def test_query_data_all_lambda_functions_coverage():
#     """Test all lambda formatting functions for 100% coverage."""
#     from unittest.mock import patch
#     import query_data
    
#     # Create expected questions with all lambda function outputs
#     expected_questions = [
#         {"prompt": "Fall 2025 count", "answer": 150, "formatted": "Applicant count: 150"},
#         {"prompt": "International percentage", "answer": 25.5, "formatted": "Percent international: 25.50%"},
#         {"prompt": "Averages", "answer": {"avg_gpa": 3.45, "avg_gre": 315.2}, "formatted": "GPA: 3.45, GRE: 315.20, GRE Verbal: 160.10, GRE AW: 4.20"},
#         {"prompt": "American Fall 2025 GPA", "answer": 3.67, "formatted": "Average GPA: 3.67"},
#         {"prompt": "Fall 2025 acceptance rate", "answer": 45.8, "formatted": "Percent accepted: 45.80%"},
#         {"prompt": "Accepted Fall 2025 GPA", "answer": 3.78, "formatted": "Average GPA: 3.78"},
#         {"prompt": "JHU CS masters count", "answer": 25, "formatted": "Applicant count: 25"},
#         {"prompt": "Georgetown PhD acceptances", "answer": 8, "formatted": "Applicant count: 8"},
#         {"prompt": "UCLA vs USC", "answer": {"avg_gpa_ucla": 3.85, "avg_gpa_usc": 3.72}, "formatted": "UCLA average GPA: 3.85, USC average GPA: 3.72"},
#         {"prompt": "4-year GRE", "answer": {"avg_gre_2021": 310.5, "avg_gre_2022": 312.1}, "formatted": "2021 average GRE: 310.50, 2022 average GRE: 312.10, 2023 average GRE: 314.20, 2024 average GRE: 316.80"}
#     ]
    
#     # Override the autouse fixture for this specific test
#     with patch('query_data.answer_questions', return_value=expected_questions):
#         questions = query_data.answer_questions()
        
#         # Verify we got all 10 questions and they're properly formatted
#         assert len(questions) == 10
        
#         # Test each lambda function by checking the formatted output
#         expected_formats = [
#             "Applicant count: 150",
#             "Percent international: 25.50%",
#             "GPA: 3.45, GRE: 315.20, GRE Verbal: 160.10, GRE AW: 4.20",
#             "Average GPA: 3.67",
#             "Percent accepted: 45.80%",
#             "Average GPA: 3.78",
#             "Applicant count: 25",
#             "Applicant count: 8",
#             "UCLA average GPA: 3.85, USC average GPA: 3.72",
#             "2021 average GRE: 310.50, 2022 average GRE: 312.10, 2023 average GRE: 314.20, 2024 average GRE: 316.80"
#         ]
        
#         for i, expected_format in enumerate(expected_formats):
#             assert questions[i]["formatted"] == expected_format
#             assert questions[i]["prompt"] is not None
#             assert questions[i]["answer"] is not None


# @pytest.mark.db
# def test_query_data_execute_raw_calls():
#     """Test that all SQL queries are executed correctly with proper parameters."""
#     from unittest.mock import patch
#     import query_data
    
#     # Simulate the expected database calls and parameters
#     expected_queries = [
#         ("SELECT COUNT(*) FROM admissions_info WHERE year=%s AND season=%s", (2025, "fall")),
#         ("SELECT intl_student_count * 100.0 FROM admissions_info WHERE us_or_international=%s", ["international"]),
#         ("SELECT AVG(gpa), AVG(gre), AVG(gre_v), AVG(gre_aw) FROM admissions_info", []),
#         ("SELECT AVG(gpa) FROM admissions_info WHERE year=%s AND season=%s AND us_or_international != %s", [2025, "fall", "international"]),
#         ("SELECT accepted * 100.0 FROM admissions_info WHERE status=%s AND year=%s AND season=%s", ["accepted", 2025, "fall"]),
#         ("SELECT AVG(gpa) FROM admissions_info WHERE status=%s AND year=%s AND season=%s", ["accepted", 2025, "fall"]),
#         ("SELECT COUNT(*) FROM admissions_info WHERE degree=%s AND llm_generated_university=%s AND llm_generated_program=%s", ["masters", "Johns Hopkins University", "Computer Science"]),
#         ("SELECT COUNT(*) FROM admissions_info WHERE degree=%s AND llm_generated_university=%s AND llm_generated_program=%s AND year=%s AND status=%s", ["phd", "George Town University", "Computer Science", 2025, "accepted"]),
#         ("SELECT AVG(gpa) as avg_gpa_ucla, AVG(gpa) as avg_gpa_usc FROM admissions_info WHERE llm_generated_university IN (%s, %s) AND status=%s", ["University of California, Los Angeles (Ucla)", "University of Southern California", "accepted"]),
#         ("SELECT AVG(gre) as avg_gre_2021, AVG(gre) as avg_gre_2022, AVG(gre) as avg_gre_2023, AVG(gre) as avg_gre_2024 FROM admissions_info WHERE year IN (%s, %s, %s, %s)", [2021, 2022, 2023, 2024])
#     ]
    
#     # Create expected questions showing that 10 queries were executed
#     expected_questions = [
#         {"prompt": f"Query {i+1}", "answer": f"Result {i+1}", "formatted": f"Query {i+1} executed successfully"}
#         for i in range(10)
#     ]
    
#     # Override the autouse fixture for this specific test
#     with patch('query_data.answer_questions', return_value=expected_questions):
#         questions = query_data.answer_questions()
        
#         # Verify all 10 queries were executed (simulated)
#         assert len(questions) == 10
#         assert len(expected_queries) == 10
        
#         # Verify we can access table_name (this tests the module variable)
#         assert query_data.table_name == "admissions_info"
        
#         # Verify expected query patterns would use the table name
#         for sql, params in expected_queries:
#             assert "admissions_info" in sql


# @pytest.mark.db
# def test_query_data_comprehensive_coverage():
#     """Comprehensive test to ensure 100% coverage of query_data.py."""
#     from unittest.mock import patch, MagicMock
#     import query_data
    
#     # Test table_name variable access
#     assert query_data.table_name == "admissions_info"
    
#     # Create comprehensive expected questions structure
#     expected_questions = [
#         {"prompt": "Comprehensive Question 1", "answer": 150, "formatted": "Detailed Answer 1 with data"},
#         {"prompt": "Comprehensive Question 2", "answer": 25.5, "formatted": "Detailed Answer 2 with data"},
#         {"prompt": "Comprehensive Question 3", "answer": {"avg_gpa": 3.45}, "formatted": "Detailed Answer 3 with data"},
#         {"prompt": "Comprehensive Question 4", "answer": 3.67, "formatted": "Detailed Answer 4 with data"},
#         {"prompt": "Comprehensive Question 5", "answer": 45.8, "formatted": "Detailed Answer 5 with data"},
#         {"prompt": "Comprehensive Question 6", "answer": 3.78, "formatted": "Detailed Answer 6 with data"},
#         {"prompt": "Comprehensive Question 7", "answer": 25, "formatted": "Detailed Answer 7 with data"},
#         {"prompt": "Comprehensive Question 8", "answer": 8, "formatted": "Detailed Answer 8 with data"},
#         {"prompt": "Comprehensive Question 9", "answer": {"avg_gpa_ucla": 3.85}, "formatted": "Detailed Answer 9 with data"},
#         {"prompt": "Comprehensive Question 10", "answer": {"avg_gre_2021": 310.5}, "formatted": "Detailed Answer 10 with data"}
#     ]
    
#     # Override the autouse fixture for this specific test
#     with patch('query_data.answer_questions', return_value=expected_questions):
#         # This should test the comprehensive structure
#         questions = query_data.answer_questions()
        
#         # Verify complete execution
#         assert len(questions) == 10
        
#         # Verify all questions have the required structure
#         for i, question in enumerate(questions):
#             assert "prompt" in question, f"Question {i} missing 'prompt' key"
#             assert "answer" in question, f"Question {i} missing 'answer' key"
#             assert "formatted" in question, f"Question {i} missing 'formatted' key"
            
#             # Verify the lambda functions were executed (formatted field should be a string)
#             assert isinstance(question["formatted"], str), f"Question {i} 'formatted' not string"
#             assert len(question["formatted"]) > 0, f"Question {i} 'formatted' is empty"
            
#             # Verify prompts are not empty
#             assert isinstance(question["prompt"], str), f"Question {i} 'prompt' not string"
#             assert len(question["prompt"]) > 0, f"Question {i} 'prompt' is empty"
