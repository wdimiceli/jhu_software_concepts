Setup and Configuration
========================

Prerequisites
-------------

* Python 3.10+
* PostgreSQL 14+

Installation
------------

1. **Create virtual environment**::

    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate

2. **Install dependencies**::

    pip install -r requirements.txt

Running the Application
-----------------------

**Start server**::

    PYTHONPATH=src python -c "import run;run.start()"

Application available at http://localhost:8080

**Start with data loading**::

    PYTHONPATH=src DATA_FILE=src/admissions_info.json python -c "import run;run.start()"

Running Tests
-------------

**All tests**::

    PYTHONPATH=src pytest -m "web or buttons or analysis or db or integration" --cov=src --cov-report=html

**By category**::

    PYTHONPATH=src pytest -m web          # Flask tests
    PYTHONPATH=src pytest -m buttons      # Button tests
    PYTHONPATH=src pytest -m analysis     # Analysis tests
    PYTHONPATH=src pytest -m db           # Database tests
    PYTHONPATH=src pytest -m integration  # Integration tests

Environment Variables
---------------------

PostgreSQL configuration:

* ``DATABASE_URL``: Host for Postgres server
* ``PG_PORT``: Port for Postgres server
* ``PG_USER``: Postgres user for the project
* ``PG_DB``: Database name

Data loading:

* ``DATA_FILE``: Path to JSON file for initial data load

Project Structure
-----------------

::

    module_4/
    ├── src/
    │   ├── run.py              # Flask application
    │   ├── model.py            # Data models
    │   ├── scrape.py           # Web scraping
    │   ├── clean.py            # Data cleaning
    │   ├── query_data.py       # Analysis queries
    │   ├── load_data.py        # Data loading
    │   ├── postgres_manager.py # Database management
    │   └── blueprints/         # Flask routes
    ├── tests/                  # Test suite
    ├── docs/                   # Documentation
