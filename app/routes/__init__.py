from flask import Blueprint
from app.routes.main import main_bp
from app.routes.another import another_bp

def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(another_bp, url_prefix='/another')
