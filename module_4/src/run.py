"""Flask application factory and startup functions.

Creates Flask app with portfolio and graduate data analysis blueprints.
Handles PostgreSQL database initialization and JSON data loading.
"""

import os
from flask import Flask
from blueprints.portfolio.routes import bp as portfolio
from blueprints.grad_data.routes import bp as grad_data
from postgres_manager import start_postgres
import load_data


def create_app() -> Flask:
    """Create Flask application with registered blueprints.

    :returns: Configured Flask application instance.
    :rtype: Flask
    """
    app = Flask(__name__)
    
    # Register the blueprint for the portfolio section.
    # This handles "/", "/contact", and "/projects".
    app.register_blueprint(portfolio)
    
    # Register the blueprint for the graduate data analysis section.
    # This handles "/grad-data/analysis".
    app.register_blueprint(grad_data, url_prefix="/grad-data")
    
    return app


def start(data_filename: str | None = None) -> None:
    """Start development server with database initialization.

    Starts PostgreSQL, loads data if specified, creates Flask app, and runs server.

    :param data_filename: Path to JSON file with admissions data. Uses DATA_FILE env var if None.
    :type data_filename: str or None
    """
    start_postgres()

    data_filename = data_filename or os.environ.get("DATA_FILE")
    if data_filename:
        load_data.load_admissions_results(data_filename)

    # Create the main Flask application instance for production.
    root_app = create_app()
    
    root_app.run(host='0.0.0.0', port=8080)
