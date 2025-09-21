"""Flask blueprint for graduate admissions data analysis routes.

This blueprint provides web routes for displaying and analyzing graduate
admissions data.
"""

import threading
import scrape
from flask import Blueprint, render_template, request
from query_data import answer_questions
import model
import postgres_manager


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


def begin_refresh() -> None:
    """Execute background data scraping and database updates.
    
    Updates global scrape_state to track progress.
    """
    global scrape_state

    scrape_state["running"] = True

    try:
        latest_id = model.AdmissionResult.get_latest_id()
        print(f"Latest id: {latest_id}")

        entries = scrape.scrape_data(1, 30000, latest_id)

        conn = postgres_manager.get_connection()
        with conn.cursor() as cursor:
            for entry in entries:
                entry.clean_and_augment()
                entry.save_to_db(cursor)

        conn.commit()

        scrape_state["entries"] = entries
    finally:
        scrape_state["running"] = False


@bp.route("/analysis", methods=["GET", "POST"])
def analysis():
    """Render admissions data analysis dashboard.

    :returns: Rendered HTML template or HTTP error response.
    :rtype: str
    """
    global scrape_state

    refresh = "refresh" in request.args
    poll = "poll" in request.args

    if (request.method == "POST" or refresh) and scrape_state["running"]:
        return "Conflict occurred", 409

    if request.method == "POST" and not scrape_state["running"]:
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
