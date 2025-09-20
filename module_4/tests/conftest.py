"""Test configuration and fixtures for the Grad Café analytics application."""

import os
import io
from pathlib import Path
import pytest
from unittest.mock import MagicMock
import threading
import postgres_manager
import model
import urllib.robotparser
import urllib3
import scrape
from psycopg import sql


test_table_name = "test_admission_results"


def pytest_configure(config):
    postgres_manager.start_postgres()
    model.init_tables()
    os.environ["DB_TABLE"] = test_table_name


@pytest.fixture
def inline_threads(monkeypatch):
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
        "formatted": "Applicant count: 100",
    },
    {
        "prompt": "What percentage of entries are from international students?",
        "answer": 25.5,
        "formatted": "Percent international: 25.50%",
    },
    {
        "prompt": "What is the average GPA, GRE, GRE V, GRE AW of applicants who provide these metrics?",
        "answer": {"avg_gpa": 3.5, "avg_gre": 315.0, "avg_gre_v": 155.0, "avg_gre_aw": 4.0},
        "formatted": "GPA: 3.50, GRE: 315.00, GRE Verbal: 155.00, GRE AW: 4.00",
    },
    {
        "prompt": "What is the average GPA of American students in Fall 2025?",
        "answer": 3.6,
        "formatted": "Average GPA: 3.60",
    },
    {
        "prompt": "What percent of entries for Fall 2025 are Acceptances?",
        "answer": 45.5,
        "formatted": "Percent accepted: 45.50%",
    },
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


# @pytest.fixture
# def mock_database_write():
#     """Mock database operations for unit tests."""
#     with patch("postgres_manager.get_connection") as mock_conn:
#         mock_cursor = MagicMock()
#         mock_conn.return_value.cursor.return_value.__enter__.return_value = mock_cursor
#         mock_cursor.fetchall.return_value = []
#         yield mock_cursor


# @pytest.fixture
# def mock_admission_result(mocker):
#     """Create a fake AdmissionResult for testing."""
#     from model import AdmissionResult

#     def create_fake_admission_result(
#         id_val=1,
#         school="Test University",
#         program="Computer Science",
#         status="accepted",
#         region="american",
#         gpa=3.8,
#         gre=320,
#     ):
#         result = AdmissionResult(
#             id=id_val,
#             school=school,
#             program_name=program,
#             degree_type="masters",
#             added_on=datetime(2024, 1, 1),
#             decision_status=status,
#             decision_date=datetime(2024, 2, 1),
#             season="fall",
#             year=2025,
#             applicant_region=region,
#             gre_general=gre,
#             gre_verbal=160,
#             gre_analytical_writing=4.5,
#             gpa=gpa,
#             comments="Great program!",
#             full_info_url=f"/result/{id_val}",
#             llm_generated_program=None,
#             llm_generated_university=None,
#         )

#         # mocker.patch.object(result, "clean_and_augment")

#         # def fake_save_to_db():
#         #     mock_database_write.execute("INSERT INTO fake_table ...")

#         # mocker.patch.object(result, "save_to_db", fake_save_to_db)

#         return result

#     return {
#         "create_fake_admission_result": create_fake_admission_result,
#     }


# @pytest.fixture
# def mock_scraper(mocker, mock_admission_result):
#     """Mock scraper that returns fake admission results."""
#     fake_scrape_results = [
#         mock_admission_result["create_fake_admission_result"](
#             1, "Test University", "Computer Science", "accepted", "american", 3.8, 320
#         ),
#         mock_admission_result["create_fake_admission_result"](
#             2, "Elite Tech Institute", "Data Science", "rejected", "international", 3.9, 335
#         ),
#         mock_admission_result["create_fake_admission_result"](
#             3, "State University", "Electrical Engineering", "waitlisted", "american", 3.6, 315
#         ),
#     ]

#     return {
#         "scrape_data": mocker.patch("scrape.scrape_data", return_value=fake_scrape_results),
#         "fake_results": fake_scrape_results,
#     }


@pytest.fixture
def mock_answer_questions():
    """Mock answer_questions to return properly formatted data."""
    return MOCK_QUESTIONS_DATA


@pytest.fixture
def mock_llm(mocker):
    """Patch `clean._load_llm` to return a mock LLM."""
    mock_llm_instance = mocker.Mock()

    # Define a fake response
    fake_response = {
        "choices": [
            {
                "message": {
                    "content": "Mocked response text"
                }
            }
        ]
    }

    # Mock the method to return the fake response
    mock_llm_instance.create_chat_completion.return_value = fake_response

    return mocker.patch("clean._load_llm", return_value=mock_llm_instance)


@pytest.fixture
def empty_table(mocker):
    """Create an empty table with the same schema as admission_result."""
    from model import DB_TABLE

    create_table_sql = sql.SQL("""
        CREATE TABLE IF NOT EXISTS {} 
        (LIKE {} INCLUDING ALL);
        TRUNCATE TABLE {} RESTART IDENTITY;
    """).format(
        sql.Identifier(test_table_name),
        sql.Identifier(DB_TABLE),
        sql.Identifier(test_table_name),
    )

    try:
        with postgres_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
            conn.commit()

        yield test_table_name

    finally:
        # Cleanup after test
        with postgres_manager.get_connection() as conn:
            with conn.cursor() as cur:
                query = sql.SQL("DROP TABLE IF EXISTS {};").format(sql.Identifier(test_table_name))

                cur.execute(query)
            conn.commit()


@pytest.fixture
def mock_robotparser(mocker):
    """Return a function to mock RobotFileParser."""
    mock_parser = MagicMock(spec=urllib.robotparser.RobotFileParser)
    mock_parser.can_fetch.return_value = True

    mocker.patch("urllib.robotparser.RobotFileParser", return_value=mock_parser)

    return mock_parser


@pytest.fixture
def mock_scrape(mocker, mock_robotparser, empty_table, mock_llm, inline_threads):
    """Fake urllib3 response object containing HTML read from a local file."""
    file_path = "path/to/your/file.html"

    # Read the HTML file from disk
    file_path = Path(__file__).parent / "fixture_data" / "www_thegradcafe_com_survey_?page=1.html"
    with open(file_path, "rb") as f:
        html_bytes = f.read()

    # Wrap in a fake HTTPResponse (like urllib3 would return)
    response = urllib3.response.HTTPResponse(
        body=io.BytesIO(html_bytes),
        status=200,
        headers={"Content-Type": "text/html"},
        preload_content=True,
    )

    # Patch urllib3.PoolManager.request to return our fake response
    mocker.patch("scrape.urllib3.PoolManager.request", return_value=response)

    original_scrape_page = scrape.scrape_page

    def wrapper(*args, **kwargs):
        results, has_more_pages = original_scrape_page(*args, **kwargs)
        # Override has_more_pages
        has_more_pages = False
        return results, has_more_pages

    mocker.patch("scrape.scrape_page", side_effect=wrapper)

    return response
