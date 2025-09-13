from flask import Flask
from blueprints.portfolio import bp as portfolio

root_app = Flask(__name__)

# Bring in the "/", "/contact", and "/projects" routes
root_app.register_blueprint(portfolio)

# Start up the server
if __name__ == "__main__":
    root_app.run(host='0.0.0.0', port=8080)
