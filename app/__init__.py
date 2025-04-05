import os
from flask import Flask, jsonify
from app.config import Config
from app.logger import configure_logging
from app.routes import register_blueprints

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Configure logging
    configure_logging(app)

    # Register Blueprints (modular routing)
    register_blueprints(app)

    # Global error handlers for better robustness
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.error("404 Not Found: %s", error)
        return jsonify({'error': 'Resource not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error("500 Internal Server Error: %s", error)
        return jsonify({'error': 'Internal server error'}), 500

    return app
