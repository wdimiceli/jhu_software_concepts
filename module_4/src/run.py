"""Main application entry point for the web server."""

import os
from flask import Flask
from blueprints.portfolio.routes import bp as portfolio
from blueprints.grad_data.routes import bp as grad_data

from postgres_manager import start_postgres


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configure app
    if config:
        app.config.update(config)
    
    # Register the blueprint for the portfolio section.
    # This handles "/", "/contact", and "/projects".
    app.register_blueprint(portfolio)
    
    # Register the blueprint for the graduate data analysis section.
    # This handles "/grad-data/analysis".
    app.register_blueprint(grad_data, url_prefix="/grad-data")
    
    return app


# Create the main Flask application instance for production.
root_app = create_app()

if __name__ == "__main__":
    """Start up the development server."""
    start_postgres()
    
    # Load data on startup if enabled
    if os.getenv('LOAD_DATA_ON_STARTUP', 'true').lower() == 'true':
        try:
            from load_data import load_data_if_available
            load_data_if_available()
        except ImportError as e:
            print(f"Could not import data loading module: {e}")
        except Exception as e:
            print(f"Data loading failed during startup: {e}")
    
    root_app.run(host='0.0.0.0', port=8080)
