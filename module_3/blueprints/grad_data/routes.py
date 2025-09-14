"""Routes for displaying and analyzing graduate admissions data.

This blueprint handles all web routes related to the admissions data
summary and analysis pages. It fetches data from the database, processes
it for display, and renders the corresponding HTML templates.
"""

from flask import Blueprint, render_template
from query_data import answer_questions


blueprint_name = "grad_data"


# Create the Blueprint instance. This handles all routes for the graduate data section.
bp = Blueprint(
    blueprint_name,
    __name__,
    template_folder="templates",
)


@bp.route("/analysis")
def analysis():
    """Render the admissions data analysis HTML template.

    This function fetches a predefined set of questions and their answers from
    the `query_data` module and passes them to the `analysis.html` template.
    """
    # Get the list of questions and their pre-calculated answers.
    props = {
        "questions": answer_questions(),
    }

    # Render the HTML template with the prepared properties.
    return render_template("analysis.html", **props)
