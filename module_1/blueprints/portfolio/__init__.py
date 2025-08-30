from flask import Blueprint, render_template

blueprint_name = "portfolio"

bp = Blueprint(
    blueprint_name,
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path=f"/static-{blueprint_name}",
)


@bp.route("/")
def home():
    return render_template("pages/home.html", page_id="home")


@bp.route("/contact")
def contact():
    return render_template("pages/contact.html")


@bp.route("/projects")
def projects():
    return render_template("pages/projects.html")
