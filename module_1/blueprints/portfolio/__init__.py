from flask import Blueprint, render_template

blueprint_name = "portfolio"

bp = Blueprint(
    blueprint_name,
    __name__,
    template_folder="templates",
    static_folder="static",

    # Give static files a unique prefix to avoid collisions with other blueprint modules.
    static_url_path=f"/static-{blueprint_name}",
)


@bp.route("/")
def home():
    """Render the homepage HTML template"""
    return render_template("pages/home.html")


@bp.route("/contact")
def contact():
    """Render the contact page HTML template"""
    return render_template("pages/contact.html")


@bp.route("/projects")
def projects():
    """Render the projects page HTML template"""
    return render_template("pages/projects.html")
