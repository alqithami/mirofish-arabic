"""MiroFish backend application factory."""

import os
import warnings

# Suppress noisy multiprocessing resource_tracker warnings from optional third-party libraries.
# This should be configured before the rest of the application imports.
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS

from .config import Config
from .utils.logger import setup_logger, get_logger
from .utils.lazy_import import lazy_symbol


def create_app(config_class=Config):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Return multilingual JSON text without ASCII escaping.
    if hasattr(app, 'json') and hasattr(app.json, 'ensure_ascii'):
        app.json.ensure_ascii = False
    
    # Configure logging.
    logger = setup_logger('mirofish')
    
    # Only log startup from the reloader child process to avoid duplicate logs in debug mode.
    is_reloader_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    debug_mode = app.config.get('DEBUG', False)
    should_log_startup = not debug_mode or is_reloader_process
    
    if should_log_startup:
        logger.info("=" * 50)
        logger.info("Starting MiroFish backend...")
        logger.info("=" * 50)
    
    # Enable CORS for the API.
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register simulation cleanup when the simulation stack is available.
    try:
        SimulationRunner = lazy_symbol('app.services.simulation_runner', 'SimulationRunner')
        SimulationRunner.register_cleanup()
        if should_log_startup:
            logger.info("Registered simulation cleanup hooks")
    except Exception as exc:
        logger.warning("Simulation cleanup hooks were not registered yet: %s", exc)
    
    # Request logging middleware.
    @app.before_request
    def log_request():
        logger = get_logger('mirofish.request')
        logger.debug(f"Request: {request.method} {request.path}")
        if request.content_type and 'json' in request.content_type:
            logger.debug(f"Payload: {request.get_json(silent=True)}")
    
    @app.after_request
    def log_response(response):
        logger = get_logger('mirofish.request')
        logger.debug(f"Response: {response.status_code}")
        return response
    
    # Register blueprints.
    from .api import graph_bp, simulation_bp, report_bp
    app.register_blueprint(graph_bp, url_prefix='/api/graph')
    app.register_blueprint(simulation_bp, url_prefix='/api/simulation')
    app.register_blueprint(report_bp, url_prefix='/api/report')
    
    # Health check endpoint.
    @app.route('/health')
    def health():
        return {'status': 'ok', 'service': 'MiroFish Backend'}
    
    if should_log_startup:
        logger.info("MiroFish backend is ready")
    
    return app

