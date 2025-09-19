"""Test configuration and fixtures for the Grad Café analytics application."""

import os
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import threading

# Add src to path so we can import our modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


@pytest.fixture
def inline_threads(monkeypatch, autouse=True):
    """Patch threading.Thread to run targets inline instead of spawning threads."""
    def fake_start(self):
        if self._target:
            self._target(*self._args, **self._kwargs)

    monkeypatch.setattr(threading.Thread, "start", fake_start)


# Mock data for answer_questions
MOCK_QUESTIONS_DATA = [
    {
        "prompt": "How many entries do you have in your database who have applied for Fall 2025?",
        "answer": 100,
        "formatted": "Applicant count: 100"
    },
    {
        "prompt": "What percentage of entries are from international students?",
        "answer": 25.5,
        "formatted": "Percent international: 25.50%"
    },
    {
        "prompt": "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",
        "answer": {"avg_gpa": 3.5, "avg_gre": 315.0, "avg_gre_v": 155.0, "avg_gre_aw": 4.0},
        "formatted": "GPA: 3.50, GRE: 315.00, GRE Verbal: 155.00, GRE AW: 4.00"
    },
    {
        "prompt": "What is the average GPA of American students in Fall 2025?",
        "answer": 3.6,
        "formatted": "Average GPA: 3.60"
    },
    {
        "prompt": "What percent of entries for Fall 2025 are Acceptances?",
        "answer": 45.5,
        "formatted": "Percent accepted: 45.50%"
    }
]


@pytest.fixture
def app():
    """Create application for testing."""
    from run import create_app
    
    app = create_app()
    
    # Create application context
    with app.app_context():
        yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test runner for the Flask application's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def mock_scraper(mocker):
    """Mock scraper that returns fake admission results."""
    def create_fake_admission_result(id_val=1, school="Test University", program="Computer Science",
                                   status="accepted", region="american", gpa=3.8, gre=320):
        """Create a fake AdmissionResult for testing."""
        from model import AdmissionResult

        result = AdmissionResult(
            id=id_val,
            school=school,
            program_name=program,
            degree_type="masters",
            added_on=datetime(2024, 1, 1),
            decision_status=status,
            decision_date=datetime(2024, 2, 1),
            season="fall",
            year=2025,
            applicant_region=region,
            gre_general=gre,
            gre_verbal=160,
            gre_analytical_writing=4.5,
            gpa=gpa,
            comments="Great program!",
            full_info_url=f"/result/{id_val}",
            llm_generated_program=None,
            llm_generated_university=None
        )

        mocker.patch.object(result, "clean_and_augment")
        mocker.patch.object(result, "save_to_db")

        return result


    return {
        "scrape_data": mocker.patch("scrape.scrape_data"),
        "fake_results": [
            create_fake_admission_result(1, "Test University", "Computer Science", "accepted", "american", 3.8, 320),
            create_fake_admission_result(2, "Elite Tech Institute", "Data Science", "rejected", "international", 3.9, 335),
            create_fake_admission_result(3, "State University", "Electrical Engineering", "waitlisted", "american", 3.6, 315)
        ],
    }


@pytest.fixture
def mock_database():
    """Mock database operations for unit tests."""
    with patch('model.get_connection') as mock_conn:
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = [10]  # Default count
        mock_cursor.fetchall.return_value = []
        yield mock_cursor


@pytest.fixture
def mock_answer_questions():
    """Mock answer_questions to return properly formatted data."""
    return MOCK_QUESTIONS_DATA
