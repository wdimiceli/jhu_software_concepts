"""Routes for displaying and analyzing graduate admissions data.

This blueprint handles all web routes related to the admissions data
summary and analysis pages. It fetches data from the database, processes
it for display, and renders the corresponding HTML templates.
"""

import threading
import scrape
from flask import Blueprint, render_template, request
from query_data import answer_questions
from model import AdmissionResult


blueprint_name = "grad_data"


# Create the Blueprint instance. This handles all routes for the graduate data section.
bp = Blueprint(
    blueprint_name,
    __name__,
    template_folder="templates",
)


scrape_state = {
    "running": False,
    "entries": None,
}


def begin_refresh():
    """Scrape new data and save to the database."""
    global scrape_state

    scrape_state["running"] = True

    try:
        latest_id = AdmissionResult.get_latest_id()
        print(f"Latest id: {latest_id}")

        entries = scrape.scrape_data(1, 30000, latest_id)

        for entry in entries:
            entry.clean_and_augment()
            entry.save_to_db()

        scrape_state["running"] = False
        scrape_state["entries"] = entries

    finally:
        scrape_state["running"] = False


@bp.route("/analysis", methods=["GET", "POST"])
def analysis():
    """Render the admissions data analysis HTML template.

    This function fetches a predefined set of questions and their answers from
    the `query_data` module and passes them to the `analysis.html` template.
    """
    global scrape_state

    refresh = "refresh" in request.args
    poll = "poll" in request.args

    if request.method == "POST":
        if not scrape_state["running"]:
            threading.Thread(target=begin_refresh, daemon=True).start()

    # Get the list of questions and their pre-calculated answers.
    props = {
        "questions": answer_questions(),
        "refresh": refresh,
        "poll": poll,
        "scrape_running": scrape_state["running"],
        "last_scraped_entry_count": len(scrape_state.get("entries") or [])
    }

    # Render the HTML template with the prepared properties.
    return render_template("analysis.html", **props)
