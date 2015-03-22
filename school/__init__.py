from flask import Flask, render_template

from .frontend import frontend
from .config import Config
from .extensions import *


def create_app():
    app = Flask(__name__)

    # configure app
    app.config.from_object(Config)

    # configure extensions
    db.init_app(app)
    mail.init_app(app)
    login_manager.init_app(app)
    # TODO set flask login extra options

    @login_manager.user_loader
    def load_user(id):
        return object()

    # configure blueprints
    blueprints = [frontend]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    # handle common error pages
    @app.errorhandler(403)
    def forbidden_page(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error_page(error):
        return render_template("errors/500.html"), 500

    return app