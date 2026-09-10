"""Eagle Bot application entry point."""
from flask import Flask
from eagle_bot.channels.web import bp as web_blueprint


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["JSON_SORT_KEYS"] = False
    app.register_blueprint(web_blueprint)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
