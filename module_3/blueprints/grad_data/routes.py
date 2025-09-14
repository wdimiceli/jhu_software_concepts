"""Routes for displaying and analyzing graduate admissions data.

This blueprint handles all web routes related to the admissions data
summary and analysis pages. It fetches data from the database, processes
it for display, and renders the corresponding HTML templates.
"""

import threading
from flask import Blueprint, render_template, request
from query_data import answer_questions
from scrape import scrape_data
from model import AdmissionResult


blueprint_name = "grad_data"


# Create the Blueprint instance. This handles all routes for the graduate data section.
bp = Blueprint(
    blueprint_name,
    __name__,
    template_folder="templates",
)


scrape_is_running = False # global flag


def begin_refresh():
    """Scrape new data and save to the database."""
    global scrape_is_running

    scrape_is_running = True

    try:
        latest_id = AdmissionResult.get_latest_id()
        print(f"Latest id: {latest_id}")

        entries = scrape_data(1, stop_at_id=latest_id)

        for entry in entries:
            entry.save_to_db()

    finally:
        scrape_is_running = False


@bp.route("/analysis", methods=["GET", "POST"])
def analysis():
    """Render the admissions data analysis HTML template.

    This function fetches a predefined set of questions and their answers from
    the `query_data` module and passes them to the `analysis.html` template.
    """
    global scrape_is_running

    refresh = "refresh" in request.args

    if request.method == "POST":
        if not scrape_is_running:
            threading.Thread(target=begin_refresh, daemon=True).start()

    # Get the list of questions and their pre-calculated answers.
    props = {
        "questions": answer_questions(),
        "refresh": refresh,
        "scrape_is_running": scrape_is_running
    }

    # Render the HTML template with the prepared properties.
    return render_template("analysis.html", **props)
