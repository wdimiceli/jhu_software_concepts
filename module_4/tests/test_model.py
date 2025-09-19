"""Comprehensive tests for model.py."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


@pytest.mark.db
@pytest.mark.parametrize("recreate", [False, True])
def test_init_tables(recreate):
    """Test init_tables creates/recreates tables correctly."""
    from model import init_tables
    
    with patch('model.get_connection') as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        init_tables(recreate=recreate)
        
        calls = mock_cursor.execute.call_args_list
        if recreate:
            assert any("DROP TABLE IF EXISTS admissions_info" in str(call) for call in calls)
        assert any("CREATE TABLE IF NOT EXISTS admissions_info" in str(call) for call in calls)
        mock_conn.commit.assert_called()


@pytest.mark.db
@pytest.mark.parametrize("tags,expected", [
    # Complete tag set
    ({"fall 2024", "gpa 3.5", "gre 320", "gre v 160", "gre aw 4.5", "international"}, 
     {"season": "fall", "year": 2024, "gpa": 3.5, "gre_general": 320, "gre_verbal": 160, 
      "gre_analytical_writing": 4.5, "applicant_region": "international"}),
    # Empty tags
    (set(), {"season": None, "year": None, "gpa": None, "gre_general": None, 
             "gre_verbal": None, "gre_analytical_writing": None, "applicant_region": False}),
    # American region with short year
    ({"american", "spring 25"}, {"applicant_region": "american", "season": "spring", "year": 2025})
])
def test_tags_from_soup(tags, expected):
    """Test _tags_from_soup function with various inputs."""
    from model import _tags_from_soup
    
    result = _tags_from_soup(tags)
    for key, value in expected.items():
        assert result[key] == value


@pytest.mark.db
@pytest.mark.parametrize("decision_str,year,expected_status,should_have_date", [
    ("Accepted on 15 Mar", 2024, "accepted", True),
    ("Invalid format", 2024, None, False)
])
def test_decision_from_soup(decision_str, year, expected_status, should_have_date):
    """Test _decision_from_soup function."""
    from model import _decision_from_soup
    
    status, date = _decision_from_soup(decision_str, year)
    assert status == expected_status
    assert (date is not None) == should_have_date


@pytest.mark.db
def test_decision_from_soup_error_handling():
    """Test _decision_from_soup ValueError and future date handling."""
    from model import _decision_from_soup
    from unittest.mock import patch
    
    # Test ValueError in date parsing
    with patch('model.datetime') as mock_dt:
        mock_dt.strptime.side_effect = ValueError("Invalid date")
        mock_dt.now.return_value.year = 2024
        
        status, date = _decision_from_soup("Accepted on 30 Feb", 2024)
        assert status == "accepted"
        assert date is None
        
        # Test future date handling
        mock_dt.strptime.side_effect = None
        mock_parsed = MagicMock()
        mock_parsed.__gt__ = MagicMock(return_value=True)  # Future date
        mock_parsed.replace.return_value = datetime(2023, 6, 15)
        mock_dt.strptime.return_value = mock_parsed
        mock_dt.now.return_value = datetime(2024, 1, 1)
        
        status, date = _decision_from_soup("Accepted on 15 Jun", 2024)
        assert status == "accepted"


@pytest.mark.db
@pytest.mark.parametrize("where,expected_params", [
    ({"year": 2024, "season": "fall"}, [2024, "fall"]),
    ({"year": 2024, "season": None}, [2024]),  # None values filtered
    ({}, [])  # Empty conditions
])
def test_build_where_clause(where, expected_params):
    """Test _build_where_clause function."""
    from model import _build_where_clause
    
    where_clause, params = _build_where_clause(where)
    assert params == expected_params
    if expected_params:
        assert "WHERE" in where_clause
    else:
        assert where_clause == ""


@pytest.mark.db
def test_admission_result_database_methods():
    """Test AdmissionResult count, fetch, execute_raw, and get_latest_id methods."""
    from model import AdmissionResult
    
    with patch('model.get_connection') as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Test count
        mock_cursor.fetchone.return_value = [42]
        assert AdmissionResult.count({"year": 2024}) == 42
        
        # Test execute_raw
        mock_cursor.execute.return_value.fetchall.return_value = [{"id": 1}]
        result = AdmissionResult.execute_raw("SELECT * FROM test", [])
        assert result == [{"id": 1}]
        
        # Test get_latest_id with result
        mock_cursor.fetchone.return_value = [123]
        assert AdmissionResult.get_latest_id() == 123
        
        # Test get_latest_id with no result
        mock_cursor.fetchone.return_value = None
        assert AdmissionResult.get_latest_id() == 0


@pytest.mark.db
def test_admission_result_from_dict():
    """Test AdmissionResult.from_dict method including program/term field removal."""
    from model import AdmissionResult
    
    test_dict = {
        "id": 123, "school": "Test University", "program_name": "Computer Science",
        "degree_type": "masters", "added_on": "2024-01-01T00:00:00",
        "decision_status": "accepted", "decision_date": "2024-02-01T00:00:00",
        "season": "fall", "year": 2024, "applicant_region": "american",
        "gre_general": 320, "gre_verbal": 160, "gre_analytical_writing": 4.5,
        "gpa": 3.8, "comments": "Great program", "full_info_url": "/result/123",
        "llm_generated_program": "Computer Science", "llm_generated_university": "Test University",
        "program": "Should be deleted", "term": "Should be deleted"
    }
    
    result = AdmissionResult.from_dict(test_dict)
    assert result.id == 123
    assert result.school == "Test University"
    assert isinstance(result.added_on, datetime)
    assert isinstance(result.decision_date, datetime)


@pytest.mark.db
def test_admission_result_save_to_db():
    """Test AdmissionResult.save_to_db method with success and exception cases."""
    from model import AdmissionResult
    
    result = AdmissionResult(
        id=123, school="Test University", program_name="Computer Science",
        degree_type="masters", added_on=datetime(2024, 1, 1),
        decision_status="accepted", decision_date=datetime(2024, 2, 1),
        season="fall", year=2024, applicant_region="american",
        gre_general=320, gre_verbal=160, gre_analytical_writing=4.5,
        gpa=3.8, comments="Great program", full_info_url="/result/123",
        llm_generated_program="Computer Science", llm_generated_university="Test University"
    )
    
    with patch('model.get_connection') as mock_get_conn:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        
        # Test successful save
        result.save_to_db()
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
        
        # Test exception handling
        mock_cursor.execute.side_effect = Exception("Database error")
        with pytest.raises(Exception, match="Database error"):
            result.save_to_db()


@pytest.mark.db
def test_admission_result_clean_and_augment():
    """Test AdmissionResult.clean_and_augment method with mocked LLM."""
    from model import AdmissionResult
    
    result = AdmissionResult(
        id=123, school="Test University", program_name="Computer Science",
        degree_type="masters", added_on=datetime(2024, 1, 1),
        decision_status="accepted", decision_date=datetime(2024, 2, 1),
        season="fall", year=2024, applicant_region="american",
        gre_general=320, gre_verbal=160, gre_analytical_writing=4.5,
        gpa=3.8, comments="Great program", full_info_url="/result/123",
        llm_generated_program=None, llm_generated_university=None
    )
    
    with patch('model.call_llm') as mock_llm:
        mock_llm.return_value = {
            "standardized_program": "Computer Science",
            "standardized_university": "Test University"
        }
        
        result.clean_and_augment()
        
        assert result.llm_generated_program == "Computer Science"
        assert result.llm_generated_university == "Test University"
        mock_llm.assert_called_once_with("Computer Science, Test University")


@pytest.mark.db
def test_from_soup_error_scenarios():
    """Test AdmissionResult.from_soup error handling scenarios."""
    from model import AdmissionResult
    from unittest.mock import patch, MagicMock
    from bs4.element import Tag
    
    def create_mock_table_row(school="Test University", program="Computer Science", 
                             date="January 1, 2024", decision="Accepted on 15 Mar", 
                             href="/result/12345"):
        mock_table_columns = MagicMock(spec=Tag)
        mock_table_columns.find_all.return_value = [
            MagicMock(text=MagicMock(strip=MagicMock(return_value=school))),
            MagicMock(text=MagicMock(strip=MagicMock(return_value=program))),
            MagicMock(text=MagicMock(strip=MagicMock(return_value=date))),
            MagicMock(text=MagicMock(strip=MagicMock(return_value=decision)))
        ]
        
        if href:
            mock_anchor = MagicMock(spec=Tag)
            mock_anchor.__getitem__.return_value = href
            mock_table_columns.find.return_value = mock_anchor
        else:
            mock_table_columns.find.return_value = None
            
        return [mock_table_columns, None, None]
    
    mock_tags_result = {
        "season": "fall", "year": 2024, "applicant_region": "american",
        "gre_general": None, "gre_verbal": None, "gre_analytical_writing": None, "gpa": None
    }
    
    # Test ValueError in decision processing
    with patch('model._tags_from_soup', return_value=mock_tags_result):
        with patch('model._decision_from_soup', side_effect=ValueError("Invalid")):
            result = AdmissionResult.from_soup(create_mock_table_row())
            assert result.decision_status is None
            assert result.decision_date is None
    
    # Test degree type ValueError
    mock_degree = MagicMock()
    mock_degree.lower.side_effect = ValueError("Cannot process")
    with patch('model._tags_from_soup', return_value=mock_tags_result):
        with patch('model._decision_from_soup', return_value=("accepted", None)):
            with patch('re.split') as mock_split:
                mock_split.return_value = ["Computer Science", mock_degree]
                result = AdmissionResult.from_soup(create_mock_table_row())
                assert result.degree_type is None
    
    # Test non-string program_name
    with patch('model._tags_from_soup', return_value=mock_tags_result):
        with patch('model._decision_from_soup', return_value=("accepted", None)):
            with patch('re.split') as mock_split:
                mock_split.return_value = [123, None]  # Non-string program_name
                result = AdmissionResult.from_soup(create_mock_table_row())
                assert result.program_name is None
    
    # Test missing anchor
    with patch('model._tags_from_soup', return_value=mock_tags_result):
        with patch('model._decision_from_soup', return_value=("accepted", None)):
            with pytest.raises(RuntimeError, match="Failed to find result anchor"):
                AdmissionResult.from_soup(create_mock_table_row(href=""))
    
    # Test invalid href format
    with patch('model._tags_from_soup', return_value=mock_tags_result):
        with patch('model._decision_from_soup', return_value=("accepted", None)):
            with pytest.raises(RuntimeError, match="anchor href for admission result is unrecognized"):
                AdmissionResult.from_soup(create_mock_table_row(href="/invalid/path/format"))

