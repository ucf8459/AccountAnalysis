"""
QuickBooks Online (QBO) API endpoints for authentication and data retrieval.
"""

from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
import psycopg2
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import sys

from app.services.qbo_service import QBOService

load_dotenv()

qbo_bp = Blueprint('qbo', __name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

@qbo_bp.route('/auth/url', methods=['GET'])
@jwt_required()
def get_auth_url():
    """Get the QBO authorization URL."""
    print('--- QBO DEBUG: Start /auth/url endpoint ---', file=sys.stderr)
    try:
        print('QBO_DEBUG: Reading env variables...', file=sys.stderr)
        cid = os.getenv('QBO_CLIENT_ID')
        csecret = os.getenv('QBO_CLIENT_SECRET')
        qenv = os.getenv('QBO_ENVIRONMENT')
        redir = os.getenv('QBO_REDIRECT_URI')
        print('QBO_CLIENT_ID:', cid, file=sys.stderr)
        print('QBO_CLIENT_SECRET:', csecret, file=sys.stderr)
        print('QBO_ENVIRONMENT:', qenv, file=sys.stderr)
        print('QBO_REDIRECT_URI:', redir, file=sys.stderr)
        print('QBO_DEBUG: Instantiating QBOService...', file=sys.stderr)
        qbo_service = QBOService()
        print('QBO_DEBUG: Calling get_authorization_url...', file=sys.stderr)
        auth_url = qbo_service.get_authorization_url()
        print('QBO_DEBUG: Got auth_url:', auth_url, file=sys.stderr)
        return jsonify({
            'auth_url': auth_url,
            'message': 'Authorization URL generated successfully'
        }), 200
    except Exception as e:
        import traceback
        print('QBO /auth/url Exception:', str(e), file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        return jsonify({'error': f'Failed to generate auth URL: {str(e)}'}), 500

@qbo_bp.route('/auth/callback', methods=['GET'])
def auth_callback():
    """Handle QBO OAuth callback."""
    try:
        auth_code = request.args.get('code')
        realm_id = request.args.get('realmId')
        
        if not auth_code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        qbo_service = QBOService()
        tokens = qbo_service.exchange_code_for_tokens(auth_code)
        
        # Store tokens in database
        current_user_id = get_jwt_identity() if request.headers.get('Authorization') else None
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO staging.qbo_tokens (user_id, realm_id, access_token, refresh_token, expires_at, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id, realm_id) 
            DO UPDATE SET 
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at,
                updated_at = %s
        """, (
            current_user_id,
            realm_id,
            tokens['access_token'],
            tokens['refresh_token'],
            tokens['expires_at'],
            datetime.now(),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'QBO authentication successful',
            'realm_id': realm_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Authentication failed: {str(e)}'}), 500

@qbo_bp.route('/company-info', methods=['GET'])
@jwt_required()
def get_company_info():
    """Get QBO company information."""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's QBO tokens
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT realm_id, access_token, refresh_token, expires_at
            FROM staging.qbo_tokens
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (current_user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'No QBO connection found. Please authenticate first.'}), 401
        
        realm_id, access_token, refresh_token, expires_at = result
        
        # Check if token is expired and refresh if needed
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
            qbo_service = QBOService()
            new_tokens = qbo_service.refresh_access_token(refresh_token)
            access_token = new_tokens['access_token']
            
            # Update tokens in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE staging.qbo_tokens
                SET access_token = %s, refresh_token = %s, expires_at = %s, updated_at = %s
                WHERE user_id = %s AND realm_id = %s
            """, (
                new_tokens['access_token'],
                new_tokens['refresh_token'],
                new_tokens['expires_at'],
                datetime.now(),
                current_user_id,
                realm_id
            ))
            conn.commit()
            cursor.close()
            conn.close()
        
        # Get company info
        qbo_service = QBOService()
        company_info = qbo_service.get_company_info(access_token, realm_id)
        
        return jsonify({
            'company_info': company_info,
            'realm_id': realm_id
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get company info: {str(e)}'}), 500

@qbo_bp.route('/financial-summary', methods=['GET'])
@jwt_required()
def get_financial_summary():
    """Get financial summary for a specific period."""
    try:
        current_user_id = get_jwt_identity()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Get user's QBO tokens
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT realm_id, access_token, refresh_token, expires_at
            FROM staging.qbo_tokens
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (current_user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'No QBO connection found. Please authenticate first.'}), 401
        
        realm_id, access_token, refresh_token, expires_at = result
        
        # Check if token is expired and refresh if needed
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
            qbo_service = QBOService()
            new_tokens = qbo_service.refresh_access_token(refresh_token)
            access_token = new_tokens['access_token']
            
            # Update tokens in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE staging.qbo_tokens
                SET access_token = %s, refresh_token = %s, expires_at = %s, updated_at = %s
                WHERE user_id = %s AND realm_id = %s
            """, (
                new_tokens['access_token'],
                new_tokens['refresh_token'],
                new_tokens['expires_at'],
                datetime.now(),
                current_user_id,
                realm_id
            ))
            conn.commit()
            cursor.close()
            conn.close()
        
        # Get financial summary
        qbo_service = QBOService()
        financial_summary = qbo_service.get_financial_summary(access_token, realm_id, start_date, end_date)
        
        return jsonify({
            'financial_summary': financial_summary
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get financial summary: {str(e)}'}), 500

@qbo_bp.route('/monthly-revenue', methods=['GET'])
@jwt_required()
def get_monthly_revenue():
    """Get monthly revenue data for a specific year."""
    try:
        current_user_id = get_jwt_identity()
        year = request.args.get('year', datetime.now().year)
        
        # Get user's QBO tokens
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT realm_id, access_token, refresh_token, expires_at
            FROM staging.qbo_tokens
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (current_user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'No QBO connection found. Please authenticate first.'}), 401
        
        realm_id, access_token, refresh_token, expires_at = result
        
        # Check if token is expired and refresh if needed
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
            qbo_service = QBOService()
            new_tokens = qbo_service.refresh_access_token(refresh_token)
            access_token = new_tokens['access_token']
            
            # Update tokens in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE staging.qbo_tokens
                SET access_token = %s, refresh_token = %s, expires_at = %s, updated_at = %s
                WHERE user_id = %s AND realm_id = %s
            """, (
                new_tokens['access_token'],
                new_tokens['refresh_token'],
                new_tokens['expires_at'],
                datetime.now(),
                current_user_id,
                realm_id
            ))
            conn.commit()
            cursor.close()
            conn.close()
        
        # Get monthly revenue
        qbo_service = QBOService()
        monthly_revenue = qbo_service.get_monthly_revenue(access_token, realm_id, int(year))
        
        return jsonify({
            'year': year,
            'monthly_revenue': monthly_revenue
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get monthly revenue: {str(e)}'}), 500

@qbo_bp.route('/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """Get customers from QBO."""
    try:
        current_user_id = get_jwt_identity()
        
        # Get user's QBO tokens
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT realm_id, access_token, refresh_token, expires_at
            FROM staging.qbo_tokens
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (current_user_id,))
        
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not result:
            return jsonify({'error': 'No QBO connection found. Please authenticate first.'}), 401
        
        realm_id, access_token, refresh_token, expires_at = result
        
        # Check if token is expired and refresh if needed
        if expires_at and datetime.fromisoformat(expires_at) < datetime.now():
            qbo_service = QBOService()
            new_tokens = qbo_service.refresh_access_token(refresh_token)
            access_token = new_tokens['access_token']
            
            # Update tokens in database
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE staging.qbo_tokens
                SET access_token = %s, refresh_token = %s, expires_at = %s, updated_at = %s
                WHERE user_id = %s AND realm_id = %s
            """, (
                new_tokens['access_token'],
                new_tokens['refresh_token'],
                new_tokens['expires_at'],
                datetime.now(),
                current_user_id,
                realm_id
            ))
            conn.commit()
            cursor.close()
            conn.close()
        
        # Get customers
        qbo_service = QBOService()
        customers = qbo_service.get_customers(access_token, realm_id)
        
        return jsonify({
            'customers': customers
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get customers: {str(e)}'}), 500

@qbo_bp.route('/<path:subpath>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def catch_all_qbo(subpath):
    print(f'QBO CATCH-ALL: Path=/{subpath}', file=sys.stderr)
    print(f'QBO CATCH-ALL: Method={request.method}', file=sys.stderr)
    print(f'QBO CATCH-ALL: Headers={dict(request.headers)}', file=sys.stderr)
    print(f'QBO CATCH-ALL: Args={request.args}', file=sys.stderr)
    print(f'QBO CATCH-ALL: Data={request.data}', file=sys.stderr)
    return 'QBO catch-all route', 418 