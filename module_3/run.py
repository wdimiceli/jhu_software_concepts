"""Main application entry point for the web server."""

from flask import Flask
from blueprints.portfolio.routes import bp as portfolio
from blueprints.grad_data.routes import bp as grad_data

# Create the main Flask application instance.
root_app = Flask(__name__)

# Register the blueprint for the portfolio section.
# This handles "/", "/contact", and "/projects".
root_app.register_blueprint(portfolio)

# Register the blueprint for the graduate data analysis section.
# This handles "/grad-data/analysis".
root_app.register_blueprint(grad_data, url_prefix="/grad-data")

if __name__ == "__main__":
    """Start up the development server."""
    root_app.run(host='0.0.0.0', port=8080, debug=True)
