"""
Main Flask Application Factory
"""
import os
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

# Initialize extensions
db = SQLAlchemy()

def get_redis_client():
    """Get Redis client from URL"""
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    try:
        return Redis.from_url(redis_url, decode_responses=True)
    except:
        host = redis_url.split('://')[-1].split(':')[0] or 'localhost'
        port = int(redis_url.split(':')[-1]) if ':' in redis_url else 6379
        return Redis(host=host, port=port, decode_responses=True)

redis_client = get_redis_client()

def create_app(config_name='production'):
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'POSTGRES_URL',
        'postgresql://postgres:postgres@localhost:5432/agentic_logger'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    
    # Setup logging
    setup_logging(app)
    
    # Register blueprints
    from routes import api_bp, health_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(health_bp)
    
    # Register extended routes for activity logging
    from routes_extended import register_extended_routes
    register_extended_routes(app)
    
    # Register LLM processing routes
    try:
        from llm_processor import register_processing_routes, start_background_processor
        register_processing_routes(app, db)
        # Start background processor in development
        if config_name != 'production':
            start_background_processor(app, db, interval=60)
        app.logger.info('LLM processing initialized')
    except Exception as e:
        app.logger.warning(f'LLM processing not initialized: {e}')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        app.logger.error(f'Server error: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Initialize agent integration (optional - agents may not all be available)
    try:
        from agent_integration import init_agent_integration
        init_agent_integration(app)
        app.logger.info('Agent integration initialized')
    except Exception as e:
        app.logger.warning(f'Agent integration skipped: {e}')
    
    return app

def setup_logging(app):
    """Configure logging"""
    if not app.debug:
        import logging.handlers
        os.makedirs('logs', exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            'logs/agentic_logger.log',
            maxBytes=10485760,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Application startup')

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8000, debug=False)
