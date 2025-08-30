from flask import Flask
from blueprints.portfolio import bp as portfolio

app = Flask(__name__)
app.register_blueprint(portfolio)

if __name__ == "__main__":
    app.run(port=8080)
