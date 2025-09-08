#!/usr/bin/env python3
"""
Multi-LLM Chat Backend API
Flask application with REST API endpoints for chat functionality
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, stream_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import yaml
from dotenv import load_dotenv

# Import modules
from models.database import db, init_db
from models.chat_models import ChatSession, ChatMessage
from routes.chat_routes import chat_bp
from routes.history_routes import history_bp
from routes.model_routes import model_bp
from utils.config_loader import ConfigLoader
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'multi-llm-chat-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL', 
        'postgresql://chatuser:chatpassword@db:5432/multi_llm_chat'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize extensions
    CORS(app, origins=os.getenv('CORS_ORIGINS', 'http://localhost:3000').split(','))
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize database
    db.init_app(app)
    
    # Setup logging
    setup_logger()
    logger = logging.getLogger(__name__)
    
    with app.app_context():
        try:
            init_db()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    # Register blueprints
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(history_bp, url_prefix='/api')
    app.register_blueprint(model_bp, url_prefix='/api')
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }), 200
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """Root endpoint with API information"""
        return jsonify({
            'name': 'Multi-LLM Chat API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'models': '/api/models',
                'chat': '/api/chat',
                'history': '/api/history',
                'sessions': '/api/sessions'
            }
        })
    
    # WebSocket events for streaming
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid}")
        emit('connected', {'data': 'Connected to Multi-LLM Chat API'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid}")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(413)
    def too_large(error):
        return jsonify({'error': 'File too large'}), 413
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_app()
    
    # Run development server
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting Multi-LLM Chat API on port {port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🌐 CORS origins: {os.getenv('CORS_ORIGINS', 'http://localhost:3000')}")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        allow_unsafe_werkzeug=True
    )