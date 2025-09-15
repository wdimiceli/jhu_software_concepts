# Module 2: Postgres Database

<small>Course: EN.605.256.8VL.FA25</small>
<br/>
<small>Module due: 09/14/2025 11:59PM EST</small>

This module contains setup scripts, utilities, and SQL queries to load and analyize the data scraped under Module 2.  The portfolio site has been improved with the analysis results and functions to update our dataset on-the-fly.

## Requirements

* Python 3.10+

* Postgres 14+

A Postgres installation is required to run this code.  For OSX users, homebrew is the most expedient way to get started:

```sh
$ brew install postgresql
```

<small>_The codebase was developed on OSX 15.6.1.  Compatible systems should work, however the setup instructions may differ for Windows._</small>

## Getting started

To run the app, first set up your environment and install the package dependencies:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Then, execute the `load_data.py` script:

```sh
python load_data.py
```

The local Postgres instance will create a database under the `./pgdata` directory.

### Starting up the Flask server

Once you have your environment ready and loaded some data, execute the `run.py` script:

```sh
python run.py
```

Flask should confirm the app is running and print

> `* Running on http://127.0.0.1:8080`

to your terminal. Open a web browser and navigate to `http://localhost:8080` to begin browsing the app.



## Citations

Afif, Temani. n.d. “The Dots CSS Loaders Collection.” https://css-loaders.com/dots/.

“Category:Green Check Marks - Wikimedia Commons.” n.d. https://commons.wikimedia.org/wiki/Category:Green_check_marks.
