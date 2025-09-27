"""Flask blueprint for portfolio website routes.

Static page routes for portfolio sections: home, contact, and projects.
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
    """Render portfolio homepage.
    
    :returns: Rendered HTML template.
    :rtype: str
    """
    return render_template("home.html")


@bp.route("/contact")
def contact():
    """Render contact page.
    
    :returns: Rendered HTML template.
    :rtype: str
    """
    return render_template("contact.html")


@bp.route("/projects")
def projects():
    """Render projects page.
    
    :returns: Rendered HTML template.
    :rtype: str
    """
    return render_template("projects.html")
