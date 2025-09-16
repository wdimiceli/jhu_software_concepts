"""Routes for a simple portfolio website.

This blueprint handles the core navigation of a personal or portfolio site.
"""

from flask import Blueprint, render_template


blueprint_name = "portfolio"


# Create a Blueprint instance for the portfolio routes.
bp = Blueprint(
    blueprint_name,
    __name__,
    template_folder="templates",
)


@bp.route("/")
def home():
    """Render the homepage HTML template."""
    return render_template("home.html")


@bp.route("/contact")
def contact():
    """Render the contact page HTML template."""
    return render_template("contact.html")


@bp.route("/projects")
def projects():
    """Render the projects page HTML template."""
    return render_template("projects.html")
