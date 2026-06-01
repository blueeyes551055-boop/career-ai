"""
Application factory for the AI-Based Career Counselling System.
"""
import os

from flask import Flask, render_template

from config import Config
from .extensions import db, login_manager
from .ml.recommender import CareerRecommender


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)

    # init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # single shared recommender instance (lazy-loads / trains the model)
    app.recommender = CareerRecommender(app.config["MODEL_PATH"])

    # blueprints
    from .routes.main import main_bp
    from .routes.auth import auth_bp
    from .routes.student import student_bp
    from .routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    # error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # create tables on first run
    with app.app_context():
        db.create_all()

    # make a few helpers available in every template
    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_year": datetime.utcnow().year, "app_name": "Career AI"}

    return app


