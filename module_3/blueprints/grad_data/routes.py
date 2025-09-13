from math import floor
from flask import Blueprint, render_template, request, abort
from model import AdmissionResult
from query_data import answer_questions


blueprint_name = "grad_data"


bp = Blueprint(
    blueprint_name,
    __name__,
    template_folder="templates",
)


@bp.route("/")
def summary():
    """Render the admissions data summary HTML template"""
    try:
        page = int(request.args.get("page", 1))
        if page < 1:
            raise ValueError()
    except ValueError:
        abort(400)

    try:
        year = request.args.get("year")

        if year:
            year = int(year)

            if year < 2020 or year > 2025:
                raise ValueError()
    except ValueError:
        abort(400)

    limit = 10  # Hardcoded for this page

    result = AdmissionResult.fetch(page * limit, limit, where={ "year": year })

    total = result["total"]

    page_count = floor(total / limit)

    if page > page_count:
        abort(404)

    pagination_numbers = [1, 2] \
        + list(range(max(1, page - 3), min(page_count, page + 3))) \
        + [page_count - 1, page_count]
    
    facets = {
        "year": year,
    }
    
    props = {
        "total": total,
        "page": page,
        "page_count": page_count,
        "entries": result["rows"],
        "pagination_numbers": list(dict.fromkeys(pagination_numbers)),
        "facets": facets,
        "facet_query": ''.join([f"&{key}={value}" for key, value in facets.items() if value]),
    }

    return render_template("summary.html", **props)


@bp.route("/analysis")
def analysis():
    """""" 
    # Next, come up with 2 addi5onal ques5ons that you are curious to answer — formulate those ques5ons
    # in words, and then write SQL code to answe

    props = {
        "questions": answer_questions(),
    }

    return render_template("analysis.html", **props)
