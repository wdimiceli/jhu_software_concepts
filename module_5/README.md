# Module 5: Software Assurance, Static Code Analysis, and SQL Injections

<small>Course: EN.605.256.8VL.FA25</small>
<br/>
<small>Module due: 12/28/2025 11:59PM EST</small>

This module improves the code quality and security of the Grad Café Analytics system.

Read The Docs: https://jhu-software-concepts-wdimiceli.readthedocs.io/

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

**Database Configuration:**

```bash
export DATABASE_URL=postgresql://user:password@host:port/database
```

**Additional configuration:**
```bash
PG_DATA_DIR=pgdata    # Local PostgreSQL data directory (default: pgdata)
```

## Testing

```bash
PYTHONPATH=src pytest -m "web or buttons or analysis or db or integration" --cov=src --cov-report=html
```

## Citations

“Meyerweb.Com.” n.d. https://meyerweb.com/eric/tools/css/reset/.

Acsany, Philipp. 2024. “Build a Scalable Flask Web Project From Scratch.” March 22, 2024. https://realpython.com/flask-project/.

File:LinkedIn Icon.Svg - Wikimedia Commons. 2014. https://commons.wikimedia.org/wiki/File:LinkedIn_icon.svg.

File:Github Logo Svg.Svg - Wikimedia Commons. 2023. https://commons.wikimedia.org/wiki/File:Github_logo_svg.svg.

“Check If a Class Is a Dataclass in Python.” 2019. Stack Overflow. May 14, 2019. https://stackoverflow.com/questions/56106116/check-if-a-class-is-a-dataclass-in-python.

“Issues Within Code Around Leap Year Using Datetime (Beginner Help).” 2020. Stack Overflow. May 14, 2020. https://stackoverflow.com/questions/61795172/issues-within-code-around-leap-year-using-datetime-beginner-help.

Afif, Temani. n.d. "The Dots CSS Loaders Collection." https://css-loaders.com/dots/.

"Category:Green Check Marks - Wikimedia Commons." n.d. https://commons.wikimedia.org/wiki/Category:Green_check_marks.
