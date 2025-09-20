# Module 4: Pytest

<small>Course: EN.605.256.8VL.FA25</small>
<br/>
<small>Module due: 12/14/2025 11:59PM EST</small>

This module extends the Grad Café Analytics system with automated testing using Pytest.

## Requirements

* Python 3.10+
* PostgreSQL 14+

### Getting started

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Starting up the Flask server

Once you have your environment ready and loaded some data, execute `start()` in the `run` module:

```sh
PYTHONPATH=src python -c "import run;run.start()"
```

Flask should confirm the app is running and print

> `* Running on http://127.0.0.1:8080`

to your terminal. Open a web browser and navigate to `http://localhost:8080` to begin browsing the app.

### Loading data

To load an initial data set, set the `DATA_FILE` environment variable:

```sh

PYTHONPATH=src DATA_FILE=src/admissions_info.json python -c "import run;run.start()"
```

### Environment configuration

Postgres settings and connection info can be altered via the following environment variables:

```
DATABASE_URL ->  Host for Postgres server
PG_PORT      ->  Port for Postgres server
PG_USER      ->  Postgres user for the project
PG_DB        ->  Database name
```

## Testing

```bash
PYTHONPATH=src pytest -m "web or buttons or analysis or db or integration" --cov=src --cov-report=html
```

## Citations

Afif, Temani. n.d. "The Dots CSS Loaders Collection." https://css-loaders.com/dots/.

"Category:Green Check Marks - Wikimedia Commons." n.d. https://commons.wikimedia.org/wiki/Category:Green_check_marks.
