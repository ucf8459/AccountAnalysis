#!/usr/bin/env python3
"""
Main Flask application for Account Analysis.
Provides API endpoints for dashboard data and user authentication.
"""

import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    CORS(app)
    
    # Register blueprints
    from app.api.dashboard import dashboard_bp
    
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'Account Analysis API is running'
        })
    
    # Root endpoint
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Account Analysis API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/health',
                'dashboard': '/api/dashboard'
            }
        })
    
    # Dashboard page
    @app.route('/dashboard')
    def dashboard_page():
        return app.send_static_file('dashboard.html')
    
    # Account table page
    @app.route('/account-table')
    def account_table_page():
        return app.send_static_file('account_table.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = 5001  # Always use port 5001
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    
    print(f"Starting Account Analysis API on port {port}")
    print(f"Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 