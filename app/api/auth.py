"""
Authentication API endpoints for user login, logout, and session management.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import psycopg2
import bcrypt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get user from database
        cursor.execute(
            "SELECT id, username, email, password_hash, role FROM auth.users WHERE username = %s AND is_active = TRUE",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        user_id, username, email, password_hash, role = user
        
        # Verify password
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            cursor.close()
            conn.close()
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Create access token
        access_token = create_access_token(
            identity=user_id,
            additional_claims={'username': username, 'role': role}
        )
        
        # Log successful login
        cursor.execute(
            "INSERT INTO auth.user_sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)",
            (user_id, access_token, datetime.now() + timedelta(hours=1))
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout endpoint."""
    try:
        current_user_id = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Invalidate session token
        cursor.execute(
            "UPDATE auth.user_sessions SET expires_at = NOW() WHERE user_id = %s AND expires_at > NOW()",
            (current_user_id,)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Logout failed: {str(e)}'}), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current user profile."""
    try:
        current_user_id = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, email, role, created_at FROM auth.users WHERE id = %s",
            (current_user_id,)
        )
        user = cursor.fetchone()
        
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        user_id, username, email, role, created_at = user
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'created_at': created_at.isoformat() if created_at else None
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin only)."""
    try:
        # Check if user has admin role
        claims = get_jwt_identity()
        if not claims or 'role' not in claims or claims['role'] != 'finance':
            return jsonify({'error': 'Unauthorized'}), 403
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, email, role, is_active, created_at FROM auth.users ORDER BY created_at DESC"
        )
        users = cursor.fetchall()
        
        user_list = []
        for user in users:
            user_id, username, email, role, is_active, created_at = user
            user_list.append({
                'id': user_id,
                'username': username,
                'email': email,
                'role': role,
                'is_active': is_active,
                'created_at': created_at.isoformat() if created_at else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({'users': user_list}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get users: {str(e)}'}), 500

@auth_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create a new user (admin only)."""
    try:
        # Check if user has admin role
        claims = get_jwt_identity()
        if not claims or 'role' not in claims or claims['role'] != 'finance':
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'sales_team')
        
        if not username or not email or not password:
            return jsonify({'error': 'Username, email, and password are required'}), 400
        
        # Validate role
        valid_roles = ['finance', 'sales_management', 'sales_team']
        if role not in valid_roles:
            return jsonify({'error': f'Invalid role. Must be one of: {valid_roles}'}), 400
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM auth.users WHERE username = %s OR email = %s", (username, email))
        existing_user = cursor.fetchone()
        
        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Username or email already exists'}), 409
        
        # Create new user
        cursor.execute(
            "INSERT INTO auth.users (username, email, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id",
            (username, email, password_hash, role)
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'User created successfully',
            'user_id': user_id
        }), 201
        
    except Exception as e:
        return jsonify({'error': f'Failed to create user: {str(e)}'}), 500 