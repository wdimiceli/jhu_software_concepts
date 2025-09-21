Graduate Admissions Data Analysis
==================================

Flask application for scraping and analyzing TheGradCafe.com data.

.. toctree::
   :maxdepth: 2
   :caption: Contents:
   
   setup
   architecture
   api
   testing

Quick Start
-----------

1. **Install Dependencies**::

    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

2. **Configure Database** (optional)::

    export DATABASE_URL=postgresql://user:password@host:port/database

3. **Run Application**::

    PYTHONPATH=src python -c "import run;run.start()"

4. **Load Data** (optional)::

    PYTHONPATH=src DATA_FILE=src/admissions_info.json python -c "import run;run.start()"

5. **Run Tests**::

    PYTHONPATH=src pytest -m "web or buttons or analysis or db or integration" --cov=src --cov-report=html

Application available at http://localhost:8080
