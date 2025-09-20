"""Main application entry point for the web server."""

import os
from flask import Flask
from blueprints.portfolio.routes import bp as portfolio
from blueprints.grad_data.routes import bp as grad_data
from postgres_manager import start_postgres
import load_data


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Register the blueprint for the portfolio section.
    # This handles "/", "/contact", and "/projects".
    app.register_blueprint(portfolio)
    
    # Register the blueprint for the graduate data analysis section.
    # This handles "/grad-data/analysis".
    app.register_blueprint(grad_data, url_prefix="/grad-data")
    
    return app


def start(data_filename: str | None = None):
    """Start up the development server."""
    start_postgres()

    if data_filename:
        load_data.load_admissions_results(data_filename)

    # Create the main Flask application instance for production.
    root_app = create_app()
    
    root_app.run(host='0.0.0.0', port=8080)
