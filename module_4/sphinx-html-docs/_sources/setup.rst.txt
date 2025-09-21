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

Database Configuration
----------------------

**Using DATABASE_URL (recommended)**::

    export DATABASE_URL=postgresql://user:password@host:port/database
    PYTHONPATH=src python -c "import run;run.start()"

**Using default settings**::

    PYTHONPATH=src python -c "import run;run.start()"
    # Uses: postgresql://student@localhost:5432/admissions

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

**Database Configuration**

* ``DATABASE_URL``: PostgreSQL connection string (default: postgresql://student@localhost:5432/admissions)

**Other Configuration**

* ``PG_DATA_DIR``: Local PostgreSQL data directory (default: pgdata)
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
