from flask import Flask
from blueprints.portfolio.routes import bp as portfolio
from blueprints.grad_data.routes import bp as grad_data

root_app = Flask(__name__)

# Bring in the "/", "/contact", and "/projects" routes
root_app.register_blueprint(portfolio)

# Bring in "/grad-data"
root_app.register_blueprint(grad_data, url_prefix="/grad-data")

# Start up the server
if __name__ == "__main__":
    root_app.run(host='0.0.0.0', port=8080, debug=True)
