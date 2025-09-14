"""Routes for displaying and analyzing graduate admissions data.

This blueprint handles all web routes related to the admissions data
summary and analysis pages. It fetches data from the database, processes
it for display, and renders the corresponding HTML templates.
"""

from math import floor
from flask import Blueprint, render_template, request, abort
from model import AdmissionResult
from query_data import answer_questions


blueprint_name = "grad_data"


# Create the Blueprint instance. This handles all routes for the graduate data section.
bp = Blueprint(
    blueprint_name,
    __name__,
    template_folder="templates",
)


@bp.route("/")
def summary():
    """Render the admissions data summary HTML template.

    This function fetches a paginated and filtered list of admission results
    from the database and passes them to the `summary.html` template.

    Query Parameters:
        page (int): The current page number for pagination. Defaults to 1.
        year (int): The year to filter the results by. Optional.
    """
    # --- Input Validation and Pagination Setup ---
    # Attempt to get the page number from the URL query string.
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            # Abort with a 400 Bad Request if the page number is invalid.
            raise ValueError()
    except ValueError:
        abort(400)

    # Attempt to get the year from the URL query string for filtering.
    try:
        year = request.args.get("year")

        if year:
            year = int(year)

            if year < 2020 or year > 2025:
                # Abort if the year is outside the valid range.
                raise ValueError()
    except ValueError:
        abort(400)

    # Hardcoded limit for the number of entries per page.
    limit = 10

    # Fetch the admission results from the database with pagination and optional filtering.
    result = AdmissionResult.fetch(page * limit, limit, where={"year": year})

    total = result["total"]
    # Calculate the total number of pages required for the data.
    page_count = floor(total / limit)

    # Abort with a 404 Not Found error if the requested page doesn't exist.
    if page > page_count:
        abort(404)

    # Generate a list of pagination numbers to display in the UI.
    pagination_numbers = (
        [1, 2]
        + list(range(max(1, page - 3), min(page_count, page + 3)))
        + [page_count - 1, page_count]
    )

    # Store the active filters (facets) to build the query string for pagination links.
    facets = {
        "year": year,
    }

    # Prepare the dictionary of properties to be passed to the template.
    props = {
        "total": total,
        "page": page,
        "page_count": page_count,
        "entries": result["rows"],
        # Use dict.fromkeys to remove duplicate page numbers.
        "pagination_numbers": list(dict.fromkeys(pagination_numbers)),
        "facets": facets,
        "facet_query": "".join([f"&{key}={value}" for key, value in facets.items() if value]),
    }

    # Render the HTML template with the prepared properties.
    return render_template("summary.html", **props)


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
