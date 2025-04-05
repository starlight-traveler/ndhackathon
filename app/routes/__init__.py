from flask import Blueprint
from app.routes.main import main_bp

def register_blueprints(app):
    app.register_blueprint(main_bp)
