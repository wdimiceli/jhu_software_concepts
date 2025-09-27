Testing Guide
=============

Test Categories
---------------

Tests are organized using pytest markers:

* ``@pytest.mark.web``: Flask routes and page rendering
* ``@pytest.mark.buttons``: Button interactions and state management
* ``@pytest.mark.analysis``: Data formatting and display
* ``@pytest.mark.db``: Database operations and schema
* ``@pytest.mark.integration``: End-to-end workflows

Running Tests
-------------

**All tests**::

    pytest -m "web or buttons or analysis or db or integration"

**By category**::

    pytest -m web          # Flask tests
    pytest -m buttons      # Button tests
    pytest -m analysis     # Analysis tests
    pytest -m db           # Database tests
    pytest -m integration  # Integration tests

**With coverage**::

    pytest --cov=src --cov-report=html
    pytest --cov-fail-under=100

Test Selectors
--------------

Tests use ``data-testid`` attributes for stable identifiers in HTML:

* ``data-testid="pull-data-btn"``: Pull Data button
* ``data-testid="update-analysis-btn"``: Update Analysis button

Test Fixtures
-------------

**client**
    Flask test client for HTTP requests::

        def test_page_loads(client):
            response = client.get("/grad-data/analysis")
            assert response.status_code == 200

**mock_answer_questions**
    Mock analysis data with formatted percentages::

        # Returns: [{"prompt": "...", "answer": 25.5, "formatted": "Percent international: 25.50%"}, ...]

**mock_scrape**
    Mock scraper using local HTML fixture data::

        # Uses tests/fixture_data/www_thegradcafe_com_survey_?page=1.html

**empty_table**
    Clean test database table for each test::

        def test_database(empty_table):
            # Table is empty and ready for test data

**inline_threads**
    Runs background threads synchronously for testing::

        # Threading.Thread.start() runs target function inline instead of spawning thread
