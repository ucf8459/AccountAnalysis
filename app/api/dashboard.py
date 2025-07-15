"""
Dashboard API endpoints for financial data, territory performance, and KPI metrics.
"""

from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
import psycopg2
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import calendar
from app.services.qbo_service import QBOService
from decimal import Decimal

load_dotenv()

dashboard_bp = Blueprint('dashboard', __name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

@dashboard_bp.route('/financial-summary', methods=['GET'])
@jwt_required()
def get_financial_summary():
    """Get financial summary data for dashboards."""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        territory = request.args.get('territory')
        account_id = request.args.get('account_id')
        
        # Build query with filters
        query = """
            SELECT 
                customer_id,
                account_id,
                total_revenue,
                total_cogs,
                total_expenses,
                gross_profit,
                net_profit,
                period_start,
                period_end,
                region,
                territory
            FROM analytics.financial_summary
            WHERE 1=1
        """
        params = []
        
        if start_date:
            query += " AND period_start >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND period_end <= %s"
            params.append(end_date)
        
        if territory:
            query += " AND territory = %s"
            params.append(territory)
        
        if account_id:
            query += " AND account_id = %s"
            params.append(account_id)
        
        query += " ORDER BY period_start DESC"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        financial_data = []
        for row in results:
            financial_data.append({
                'customer_id': row[0],
                'account_id': row[1],
                'total_revenue': float(row[2]) if row[2] else 0,
                'total_cogs': float(row[3]) if row[3] else 0,
                'total_expenses': float(row[4]) if row[4] else 0,
                'gross_profit': float(row[5]) if row[5] else 0,
                'net_profit': float(row[6]) if row[6] else 0,
                'period_start': row[7].isoformat() if row[7] else None,
                'period_end': row[8].isoformat() if row[8] else None,
                'region': row[9],
                'territory': row[10]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'financial_summary': financial_data,
            'count': len(financial_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get financial summary: {str(e)}'}), 500

@dashboard_bp.route('/territory-performance', methods=['GET'])
@jwt_required()
def get_territory_performance():
    """Get territory performance data."""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        period_type = request.args.get('period_type', 'monthly')
        
        # Build query
        query = """
            SELECT 
                territory_name,
                total_sales,
                num_accounts,
                avg_revenue_per_account,
                report_date,
                period_type
            FROM analytics.territory_performance
            WHERE period_type = %s
        """
        params = [period_type]
        
        if start_date:
            query += " AND report_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND report_date <= %s"
            params.append(end_date)
        
        query += " ORDER BY report_date DESC, total_sales DESC"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        territory_data = []
        for row in results:
            territory_data.append({
                'territory_name': row[0],
                'total_sales': float(row[1]) if row[1] else 0,
                'num_accounts': row[2],
                'avg_revenue_per_account': float(row[3]) if row[3] else 0,
                'report_date': row[4].isoformat() if row[4] else None,
                'period_type': row[5]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'territory_performance': territory_data,
            'count': len(territory_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get territory performance: {str(e)}'}), 500

@dashboard_bp.route('/account-kpis', methods=['GET'])
@jwt_required()
def get_account_kpis():
    """Get account KPI data."""
    try:
        # Get query parameters
        territory = request.args.get('territory')
        min_revenue = request.args.get('min_revenue')
        max_revenue = request.args.get('max_revenue')
        sort_by = request.args.get('sort_by', 'revenue_per_sample')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = """
            SELECT 
                account_id,
                account_name,
                revenue_per_sample,
                cost_of_sale,
                billing_per_sample,
                collection_rate,
                territory,
                report_date
            FROM analytics.account_kpis
            WHERE 1=1
        """
        params = []
        
        if territory:
            query += " AND territory = %s"
            params.append(territory)
        
        if min_revenue:
            query += " AND revenue_per_sample >= %s"
            params.append(float(min_revenue))
        
        if max_revenue:
            query += " AND revenue_per_sample <= %s"
            params.append(float(max_revenue))
        
        # Validate sort parameters
        valid_sort_fields = ['revenue_per_sample', 'cost_of_sale', 'billing_per_sample', 'collection_rate']
        if sort_by not in valid_sort_fields:
            sort_by = 'revenue_per_sample'
        
        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'desc'
        
        query += f" ORDER BY {sort_by} {sort_order.upper()}"
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        kpi_data = []
        for row in results:
            kpi_data.append({
                'account_id': row[0],
                'account_name': row[1],
                'revenue_per_sample': float(row[2]) if row[2] else 0,
                'cost_of_sale': float(row[3]) if row[3] else 0,
                'billing_per_sample': float(row[4]) if row[4] else 0,
                'collection_rate': float(row[5]) if row[5] else 0,
                'territory': row[6],
                'report_date': row[7].isoformat() if row[7] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'account_kpis': kpi_data,
            'count': len(kpi_data)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get account KPIs: {str(e)}'}), 500

@dashboard_bp.route('/dashboard-overview', methods=['GET'])
@jwt_required()
def get_dashboard_overview():
    """Get comprehensive dashboard overview data."""
    try:
        # Get query parameters
        period_type = request.args.get('period_type', 'ytd')  # ytd, previous_month, current_month, qtd
        territory = request.args.get('territory')
        
        # Calculate date ranges based on period type
        today = datetime.now()
        if period_type == 'ytd':
            start_date = datetime(today.year, 1, 1)
            end_date = today
        elif period_type == 'previous_month':
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1)
                end_date = datetime(today.year - 1, 12, 31)
            else:
                start_date = datetime(today.year, today.month - 1, 1)
                end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
        elif period_type == 'current_month':
            start_date = datetime(today.year, today.month, 1)
            end_date = today
        elif period_type == 'qtd':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = datetime(today.year, quarter_start_month, 1)
            end_date = today
        else:
            start_date = datetime(today.year, 1, 1)
            end_date = today
        
        # Get financial summary for the period
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Query financial data
        cursor.execute("""
            SELECT 
                COALESCE(SUM(total_revenue), 0) as total_revenue,
                COALESCE(SUM(total_cogs), 0) as total_cogs,
                COALESCE(SUM(total_expenses), 0) as total_expenses,
                COALESCE(SUM(gross_profit), 0) as gross_profit,
                COALESCE(SUM(net_profit), 0) as net_profit,
                COUNT(DISTINCT account_id) as num_accounts
            FROM analytics.financial_summary
            WHERE period_start >= %s AND period_end <= %s
        """, (start_date.date(), end_date.date()))
        
        financial_data = cursor.fetchone()
        
        # Query territory performance
        cursor.execute("""
            SELECT 
                territory_name,
                total_sales,
                num_accounts,
                avg_revenue_per_account
            FROM analytics.territory_performance
            WHERE report_date >= %s AND report_date <= %s
            ORDER BY total_sales DESC
        """, (start_date.date(), end_date.date()))
        
        territory_data = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # Format response
        overview_data = {
            'period': {
                'type': period_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'financial_summary': {
                'total_revenue': float(financial_data[0]),
                'total_cogs': float(financial_data[1]),
                'total_expenses': float(financial_data[2]),
                'gross_profit': float(financial_data[3]),
                'net_profit': float(financial_data[4]),
                'num_accounts': financial_data[5]
            },
            'territory_performance': [
                {
                    'territory_name': row[0],
                    'total_sales': float(row[1]),
                    'num_accounts': row[2],
                    'avg_revenue_per_account': float(row[3])
                }
                for row in territory_data
            ]
        }
        
        return jsonify(overview_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get dashboard overview: {str(e)}'}), 500

@dashboard_bp.route('/qbo-integrated', methods=['GET'])
@jwt_required()
def get_qbo_integrated_data():
    """Get dashboard data integrated with QBO for different time periods."""
    try:
        current_user_id = get_jwt_identity()
        period_type = request.args.get('period_type', 'ytd')
        
        # Calculate date ranges based on period type
        today = datetime.now()
        if period_type == 'ytd':
            start_date = datetime(today.year, 1, 1)
            end_date = today
            year = today.year
        elif period_type == 'previous_month':
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1)
                end_date = datetime(today.year - 1, 12, 31)
                year = today.year - 1
            else:
                start_date = datetime(today.year, today.month - 1, 1)
                end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
                year = today.year
        elif period_type == 'current_month':
            start_date = datetime(today.year, today.month, 1)
            end_date = today
            year = today.year
        elif period_type == 'qtd':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = datetime(today.year, quarter_start_month, 1)
            end_date = today
            year = today.year
        else:
            start_date = datetime(today.year, 1, 1)
            end_date = today
            year = today.year
        
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
            # Return mock data if no QBO connection
            return jsonify({
                'period': {
                    'type': period_type,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'financial_summary': {
                    'total_revenue': 3350126.0,
                    'total_cogs': 730094.0,
                    'total_expenses': 1870000.0,
                    'gross_profit': 2620032.0,
                    'net_profit': 750000.0,
                    'num_accounts': 1200
                },
                'monthly_revenue': [
                    {'month': 1, 'month_name': 'Jan', 'revenue': 601822, 'income': 120000},
                    {'month': 2, 'month_name': 'Feb', 'revenue': 699211, 'income': 150000},
                    {'month': 3, 'month_name': 'Mar', 'revenue': 749359, 'income': 180000},
                    {'month': 4, 'month_name': 'Apr', 'revenue': 680788, 'income': 160000},
                    {'month': 5, 'month_name': 'May', 'revenue': 619946, 'income': 140000}
                ],
                'source': 'mock_data'
            }), 200
        
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
        
        # Get real QBO data
        qbo_service = QBOService()
        
        # Get financial summary
        financial_summary = qbo_service.get_financial_summary(
            access_token, 
            realm_id, 
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        )
        
        # Get monthly revenue for the year
        monthly_revenue = qbo_service.get_monthly_revenue(access_token, realm_id, year)
        
        return jsonify({
            'period': {
                'type': period_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'financial_summary': financial_summary,
            'monthly_revenue': monthly_revenue,
            'source': 'qbo_api'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get QBO integrated data: {str(e)}'}), 500

@dashboard_bp.route('/export', methods=['GET'])
@jwt_required()
def export_data():
    """Export dashboard data to CSV/Excel."""
    try:
        export_type = request.args.get('type', 'csv')  # csv or excel
        data_type = request.args.get('data_type')  # financial, territory, kpis
        
        if export_type not in ['csv', 'excel']:
            return jsonify({'error': 'Invalid export type. Use csv or excel'}), 400
        
        if data_type not in ['financial', 'territory', 'kpis']:
            return jsonify({'error': 'Invalid data type. Use financial, territory, or kpis'}), 400
        
        # This would implement the actual export logic
        # For now, return a placeholder response
        return jsonify({
            'message': f'Export {data_type} data as {export_type}',
            'status': 'not_implemented'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to export data: {str(e)}'}), 500

@dashboard_bp.route('/account-table', methods=['GET'])
def account_table():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'healthtech'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', ''),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    cur = conn.cursor()
    query = '''
        SELECT
            ps.practice_name,
            COUNT(ps.sample_number) AS sample_count,
            COALESCE(SUM(sb.total_charges), 0) AS total_charges,
            ROUND(CAST(COALESCE(SUM(sb.total_charges), 0) / NULLIF(COUNT(ps.sample_number), 0) AS numeric), 2) AS bps
        FROM practice_samples ps
        LEFT JOIN sample_billing sb
            ON ps.sample_number = sb.account_number
        GROUP BY ps.practice_name
        ORDER BY ps.practice_name
    '''
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    result = [
        {
            'practice_name': r[0],
            'sample_count': r[1],
            'total_charges': float(r[2]),
            'bps': float(r[3])
        }
        for r in rows
    ]
    return jsonify(result)

@dashboard_bp.route('/account-table')
def serve_account_table():
    return render_template('account_table.html') 

@dashboard_bp.route('/dev/mock-data', methods=['GET'])
def get_mock_dashboard_data():
    """Development endpoint to get mock dashboard data without authentication."""
    try:
        period_type = request.args.get('period_type', 'ytd')
        
        # Calculate date ranges based on period type
        today = datetime.now()
        if period_type == 'ytd':
            start_date = datetime(today.year, 1, 1)
            end_date = today
        elif period_type == 'previous_month':
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1)
                end_date = datetime(today.year - 1, 12, 31)
            else:
                start_date = datetime(today.year, today.month - 1, 1)
                end_date = datetime(today.year, today.month, 1) - timedelta(days=1)
        elif period_type == 'current_month':
            start_date = datetime(today.year, today.month, 1)
            end_date = today
        elif period_type == 'qtd':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            start_date = datetime(today.year, quarter_start_month, 1)
            end_date = today
        else:
            start_date = datetime(today.year, 1, 1)
            end_date = today
        
        # Return mock data based on period type
        mock_data = {
            'ytd': {
                'financial_summary': {
                    'total_revenue': 3350126.0,
                    'total_cogs': 730094.0,
                    'total_expenses': 1870000.0,
                    'gross_profit': 2620032.0,
                    'net_profit': 750000.0,
                    'num_accounts': 1200
                },
                'monthly_revenue': [
                    {'month': 1, 'month_name': 'Jan', 'revenue': 601822, 'income': 120000},
                    {'month': 2, 'month_name': 'Feb', 'revenue': 699211, 'income': 150000},
                    {'month': 3, 'month_name': 'Mar', 'revenue': 749359, 'income': 180000},
                    {'month': 4, 'month_name': 'Apr', 'revenue': 680788, 'income': 160000},
                    {'month': 5, 'month_name': 'May', 'revenue': 619946, 'income': 140000}
                ]
            },
            'previous_month': {
                'financial_summary': {
                    'total_revenue': 619946.0,
                    'total_cogs': 156094.0,
                    'total_expenses': 400000.0,
                    'gross_profit': 463852.0,
                    'net_profit': 63852.0,
                    'num_accounts': 1200
                },
                'monthly_revenue': [
                    {'month': 5, 'month_name': 'May', 'revenue': 619946, 'income': 140000}
                ]
            },
            'current_month': {
                'financial_summary': {
                    'total_revenue': 450000.0,
                    'total_cogs': 98000.0,
                    'total_expenses': 300000.0,
                    'gross_profit': 352000.0,
                    'net_profit': 52000.0,
                    'num_accounts': 1200
                },
                'monthly_revenue': [
                    {'month': 7, 'month_name': 'Jul', 'revenue': 450000, 'income': 100000}
                ]
            },
            'qtd': {
                'financial_summary': {
                    'total_revenue': 1759734.0,
                    'total_cogs': 386094.0,
                    'total_expenses': 1000000.0,
                    'gross_profit': 1373640.0,
                    'net_profit': 373640.0,
                    'num_accounts': 1200
                },
                'monthly_revenue': [
                    {'month': 4, 'month_name': 'Apr', 'revenue': 680788, 'income': 160000},
                    {'month': 5, 'month_name': 'May', 'revenue': 619946, 'income': 140000},
                    {'month': 6, 'month_name': 'Jun', 'revenue': 459000, 'income': 120000}
                ]
            }
        }
        
        data = mock_data.get(period_type, mock_data['ytd'])
        
        return jsonify({
            'period': {
                'type': period_type,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'financial_summary': data['financial_summary'],
            'monthly_revenue': data['monthly_revenue'],
            'source': 'mock_data'
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get mock data: {str(e)}'}), 500

@dashboard_bp.route('/dev/territory-data', methods=['GET'])
def get_mock_territory_data():
    """Development endpoint to get mock territory data without authentication."""
    try:
        period_type = request.args.get('period_type', 'ytd')
        
        # Mock territory data
        territory_data = {
            'territories': [
                {
                    'name': 'Alpha',
                    'revenue': 195874,
                    'gross_profit': 156699,
                    'gp_percentage': 80,
                    'cos_percentage': 20,
                    'collection_percentage': 98,
                    'num_accounts': 45,
                    'quarter_sparkline': [90, 100, 110, 120, 130, 125, 135],
                    'ytd_sparkline': [80, 85, 90, 100, 110, 120, 130],
                    'ros': 1.8
                },
                {
                    'name': 'Bravo',
                    'revenue': 133202,
                    'gross_profit': 106562,
                    'gp_percentage': 80,
                    'cos_percentage': 20,
                    'collection_percentage': 95,
                    'num_accounts': 32,
                    'quarter_sparkline': [60, 70, 80, 90, 100, 110, 120],
                    'ytd_sparkline': [50, 60, 70, 80, 90, 100, 110],
                    'ros': 1.5
                },
                {
                    'name': 'Charlie',
                    'revenue': 42662,
                    'gross_profit': 34130,
                    'gp_percentage': 80,
                    'cos_percentage': 20,
                    'collection_percentage': 92,
                    'num_accounts': 12,
                    'quarter_sparkline': [20, 25, 30, 35, 40, 38, 42],
                    'ytd_sparkline': [10, 15, 20, 25, 30, 35, 40],
                    'ros': 0.8
                },
                {
                    'name': 'Delta',
                    'revenue': 32581,
                    'gross_profit': 26065,
                    'gp_percentage': 80,
                    'cos_percentage': 20,
                    'collection_percentage': 90,
                    'num_accounts': 8,
                    'quarter_sparkline': [10, 12, 14, 16, 18, 17, 19],
                    'ytd_sparkline': [5, 7, 9, 11, 13, 15, 17],
                    'ros': 0.7
                },
                {
                    'name': 'Echo',
                    'revenue': 113725,
                    'gross_profit': 90980,
                    'gp_percentage': 80,
                    'cos_percentage': 20,
                    'collection_percentage': 97,
                    'num_accounts': 28,
                    'quarter_sparkline': [50, 60, 70, 80, 90, 100, 110],
                    'ytd_sparkline': [40, 50, 60, 70, 80, 90, 100],
                    'ros': 1.2
                },
                {
                    'name': 'Foxtrot',
                    'revenue': 63560,
                    'gross_profit': 50848,
                    'gp_percentage': 80,
                    'cos_percentage': 20,
                    'collection_percentage': 88,
                    'num_accounts': 15,
                    'quarter_sparkline': [30, 35, 40, 45, 50, 48, 52],
                    'ytd_sparkline': [20, 25, 30, 35, 40, 45, 50],
                    'ros': 0.2
                }
            ],
            'summary': {
                'total_revenue': 581604,
                'total_gp_percentage': 80,
                'total_cos_percentage': 20,
                'total_collection_percentage': 95
            }
        }
        
        return jsonify(territory_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get territory data: {str(e)}'}), 500

@dashboard_bp.route('/dev/account-data', methods=['GET'])
def get_mock_account_data():
    """Development endpoint to get mock account data without authentication."""
    try:
        territory = request.args.get('territory', 'all')
        
        # Mock account data
        all_accounts = [
            {'practice': 'Sunrise Family Medicine', 'bps': 176.21, 'rps': 107.23, 'collection': '98%', 'collector': 'Y', 'income': '$3,000', 'territory': 'Alpha'},
            {'practice': 'Green Valley Clinic', 'bps': 184.73, 'rps': 107.20, 'collection': '95%', 'collector': 'N', 'income': '$2,500', 'territory': 'Charlie'},
            {'practice': 'Downtown Pediatrics', 'bps': 169.36, 'rps': 101.68, 'collection': '99%', 'collector': 'Y', 'income': '$2,700', 'territory': 'Bravo'},
            {'practice': 'Westside Health Group', 'bps': 188.73, 'rps': 104.73, 'collection': '96%', 'collector': 'N', 'income': '$2,000', 'territory': 'Delta'},
            {'practice': 'Northside Family Care', 'bps': 198.57, 'rps': 108.56, 'collection': '92%', 'collector': 'Y', 'income': '$700', 'territory': 'Charlie'},
            {'practice': 'Central Medical Partners', 'bps': 192.72, 'rps': 89.11, 'collection': '90%', 'collector': 'N', 'income': '$600', 'territory': 'Delta'},
            {'practice': 'Eastview Pediatrics', 'bps': 184.73, 'rps': 107.20, 'collection': '97%', 'collector': 'Y', 'income': '$1,500', 'territory': 'Echo'},
            {'practice': 'Southtown Clinic', 'bps': 176.21, 'rps': 107.23, 'collection': '93%', 'collector': 'N', 'income': '$800', 'territory': 'Foxtrot'}
        ]
        
        if territory != 'all':
            accounts = [acc for acc in all_accounts if acc['territory'] == territory]
        else:
            accounts = all_accounts
        
        return jsonify({
            'accounts': accounts,
            'territory': territory,
            'count': len(accounts)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get account data: {str(e)}'}), 500

@dashboard_bp.route('/dev/account-table', methods=['GET'])
def get_mock_account_table():
    """Development endpoint to get mock account table data with new column structure."""
    try:
        period_type = request.args.get('period_type', 'ytd')

        # Mock logic for collection_pct and revenue
        account_data = [
            {
                'practice': 'Sunrise Family Medicine',
                'territory': 'Alpha',
                'revenue': 25000.00,
                'collection_pct': '98%',
                'rps': 107.23,
                'revenue_periods': 1
            },
            {
                'practice': 'Green Valley Clinic',
                'territory': 'Charlie',
                'revenue': 22500.00,
                'collection_pct': '95%',
                'rps': 107.20,
                'revenue_periods': 1
            },
            {
                'practice': 'Downtown Pediatrics',
                'territory': 'Bravo',
                'revenue': 21000.00,
                'collection_pct': '99%',
                'rps': 101.68,
                'revenue_periods': 1
            },
            {
                'practice': 'Westside Health Group',
                'territory': 'Delta',
                'revenue': 19800.00,
                'collection_pct': '96%',
                'rps': 104.73,
                'revenue_periods': 1
            },
            {
                'practice': 'Northside Family Care',
                'territory': 'Echo',
                'revenue': 18900.00,
                'collection_pct': '< 90',
                'rps': 108.56,
                'revenue_periods': 1
            },
            {
                'practice': 'Central Medical Partners',
                'territory': 'Foxtrot',
                'revenue': 17500.00,
                'collection_pct': '90%',
                'rps': 89.11,
                'revenue_periods': 1
            },
            {
                'practice': 'Eastview Pediatrics',
                'territory': 'Echo',
                'revenue': 16800.00,
                'collection_pct': '97%',
                'rps': 107.20,
                'revenue_periods': 1
            },
            {
                'practice': 'Southtown Clinic',
                'territory': 'Foxtrot',
                'revenue': 15600.00,
                'collection_pct': '93%',
                'rps': 107.23,
                'revenue_periods': 1
            },
            {
                'practice': 'Riverbend Medical',
                'territory': 'Alpha',
                'revenue': 14900.00,
                'collection_pct': '< 90',
                'rps': 103.47,
                'revenue_periods': 1
            },
            {
                'practice': 'Oakwood Family Practice',
                'territory': 'Bravo',
                'revenue': 14200.00,
                'collection_pct': '92%',
                'rps': 105.19,
                'revenue_periods': 1
            }
        ]

        # Adjust data based on period type (mock scaling)
        if period_type == 'previous_month':
            for account in account_data:
                account['revenue'] = round(account['revenue'] * 0.2, 2)
        elif period_type == 'current_month':
            for account in account_data:
                account['revenue'] = round(account['revenue'] * 0.15, 2)
        elif period_type == 'qtd':
            for account in account_data:
                account['revenue'] = round(account['revenue'] * 0.6, 2)

        return jsonify({
            'accounts': account_data,
            'period_type': period_type,
            'count': len(account_data)
        }), 200

    except Exception as e:
        return jsonify({'error': f'Failed to get account table data: {str(e)}'}), 500

def calculate_average_collection_pct(cursor, practice_name, start_date, max_periods=6):
    """
    Calculate average collection percentage for a practice across multiple historical periods.
    Starts from 3 periods back and looks at up to 6 periods total.
    Excludes zero collection periods and stops when hitting a zero collection period.
    """
    collection_pcts = []
    periods_used = 0
    
    # Start from 3 periods back
    for i in range(3, 3 + max_periods):
        # Calculate the period i months back
        target_month = (start_date.month - i) % 12 or 12
        target_year = start_date.year if start_date.month > i else start_date.year - 1
        
        period_start = datetime(target_year, target_month, 1)
        if target_month == 12:
            period_end = datetime(target_year, 12, 31)
        else:
            period_end = datetime(target_year, target_month + 1, 1) - timedelta(days=1)
        
        # Get collection data for this period
        cursor.execute('''
            SELECT COALESCE(SUM(sb.total_charges),0) as placed,
                   COALESCE(SUM(sb.total_payments),0) as collected
            FROM sample_billing sb
            JOIN account_data ad ON sb.client_account_number = ad.account_number
            WHERE ad.practice_name = %s 
            AND sb.placement_date >= %s AND sb.placement_date <= %s
        ''', (practice_name, period_start, period_end))
        
        result = cursor.fetchone()
        if result:
            placed, collected = float(result[0]), float(result[1])
            
            if placed > 0:
                collection_pct = collected / placed
                if collection_pct > 0:  # Only include non-zero collection percentages
                    collection_pcts.append(collection_pct)
                    periods_used += 1
                else:
                    # Stop when we hit a zero collection period
                    break
            else:
                # Stop when we hit a period with no placed revenue
                break
        else:
            # Stop when we hit a period with no data
            break
    
    if collection_pcts:
        return sum(collection_pcts) / len(collection_pcts), periods_used
    else:
        return None, 0

@dashboard_bp.route('/account-table-live', methods=['GET'])
def get_account_table_live():
    """Live endpoint to get account table data from the real database, grouped by practice."""
    try:
        period_type = request.args.get('period_type')
        if not period_type:
            period_type = 'month'
        
        # Use the updated get_month_name_and_range function
        month_name, start_date, end_date = get_month_name_and_range(period_type)
        if not start_date or not end_date:
            return jsonify({'error': 'Invalid period_type'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Join sample_billing and account_data, group by practice and territory
        cursor.execute('''
            SELECT ad.practice_name, ad.territory,
                   COALESCE(SUM(sb.total_charges),0) as placed_revenue,
                   COUNT(DISTINCT sb.client_account_number) as sample_count
            FROM sample_billing sb
            JOIN account_data ad ON sb.client_account_number = ad.account_number
            WHERE sb.placement_date >= %s AND sb.placement_date <= %s
            GROUP BY ad.practice_name, ad.territory
        ''', (start_date, end_date))
        rows = cursor.fetchall()

        # Get account counts per territory
        cursor.execute('''
            SELECT ad.territory, COUNT(DISTINCT ad.practice_name) as num_accounts
            FROM account_data ad
            GROUP BY ad.territory
        ''')
        territory_account_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # --- Calculate average collection % per territory (unweighted, only for practices with collection % >= 90) ---
        # REMOVED: Territory average logic - collection % should simply be the average of historical periods
        # --- End territory averages ---

        # --- Expenses by territory for the period ---
        # Determine month_year string for the period (e.g., 'March 2025')
        month_year = start_date.strftime('%B %Y')
        # Get Expenses for each territory for the period (for CPS calculation)
        cursor.execute("""
            SELECT territory, amount FROM cogs_expense
            WHERE month_year = %s AND expense_type = 'Expense'
        """, (month_year,))
        expenses_by_territory = {row[0]: Decimal(str(row[1])) for row in cursor.fetchall()}
        # Get COGS for each territory for the period (for COGS allocation)
        cursor.execute("""
            SELECT territory, amount FROM cogs_expense
            WHERE month_year = %s AND expense_type = 'COGS'
        """, (month_year,))
        cogs_by_territory = {row[0]: Decimal(str(row[1])) for row in cursor.fetchall()}
        # Get total samples per territory for the period
        cursor.execute('''
            SELECT ad.territory, COUNT(sb.client_account_number) as total_samples
            FROM sample_billing sb
            JOIN account_data ad ON sb.client_account_number = ad.account_number
            WHERE sb.placement_date >= %s AND sb.placement_date <= %s
            GROUP BY ad.territory
        ''', (start_date, end_date))
        samples_by_territory = {row[0]: row[1] for row in cursor.fetchall()}

        result = []
        total_revenue = 0
        total_cogs = 0
        total_profit = 0
        total_collector_cost = 0
        total_samples = 0
        total_collection_weighted = Decimal('0')
        total_collection_weight = Decimal('0')
        
        for row in rows:
            practice_name, territory, placed_revenue, sample_count = row
            avg_collection_pct, periods_used = calculate_average_collection_pct(cursor, practice_name, start_date)
            # Collection % calculation - simply use the average of historical periods
            if avg_collection_pct is not None:
                collection_pct_str = f"{round(avg_collection_pct*100)}%"
                used_collection_pct_decimal = Decimal(str(avg_collection_pct))
            else:
                collection_pct_str = '< 90'
                used_collection_pct_decimal = Decimal('0.9')
            placed_revenue = Decimal(str(placed_revenue))
            revenue = placed_revenue * used_collection_pct_decimal
            rps = revenue / sample_count if sample_count > 0 else Decimal('0')
            # Calculate BPS (Billing Per Sample) - total initial balance / sample count
            bps = placed_revenue / sample_count if sample_count > 0 else Decimal('0')
            # COGS allocation - use COGS per sample for territory * sample_count
            territory_cogs = cogs_by_territory.get(territory, Decimal('0'))
            territory_samples = samples_by_territory.get(territory, 0)
            cogs_per_sample = (territory_cogs / territory_samples) if territory_samples > 0 else Decimal('0')
            cogs_allocated = cogs_per_sample * sample_count
            
            # Calculate additional fields
            profit = revenue - cogs_allocated
            pps = profit / sample_count if sample_count > 0 else Decimal('0')
            # CPS = territory expenses / territory samples (not per practice)
            territory_expenses = expenses_by_territory.get(territory, Decimal('0'))
            cps = (territory_expenses / territory_samples) if territory_samples > 0 else Decimal('0')
            delta = pps - cps
            
            # Get collector status and cost
            cursor.execute("""
                SELECT collector, COALESCE(collector_cost, 0) FROM account_data 
                WHERE practice_name = %s 
                LIMIT 1
            """, (practice_name,))
            collector_result = cursor.fetchone()
            collector = collector_result[0] if collector_result else 'N'
            collector_cost = Decimal(str(collector_result[1])) if collector_result and collector_result[1] is not None else Decimal('0')
            
            # Accumulate totals
            total_revenue += revenue
            total_cogs += cogs_allocated
            total_profit += profit
            total_collector_cost += collector_cost
            total_samples += sample_count
            if used_collection_pct_decimal > 0:
                total_collection_weighted += revenue * used_collection_pct_decimal
                total_collection_weight += placed_revenue
            
            result.append({
                'practice': practice_name,
                'territory': territory,
                'revenue': round(float(revenue), 2),
                'cogs': round(float(cogs_allocated), 2),
                'profit': round(float(profit), 2),
                'collection_pct': collection_pct_str,
                'revenue_periods': periods_used,
                'rps': round(float(rps), 2),
                'bps': round(float(bps), 2),
                'pps': round(float(pps), 2),
                'cps': round(float(cps), 2),
                'delta': round(float(delta), 2),
                'collector': collector,
                'collector_cost': round(float(collector_cost), 2),
                'sample_count': sample_count
            })

        # Calculate averages
        avg_cogs = total_cogs / len(result) if result else Decimal('0')
        avg_rps = total_revenue / total_samples if total_samples > 0 else Decimal('0')
        avg_pps = total_profit / total_samples if total_samples > 0 else Decimal('0')
        # Average CPS = total expenses / total samples
        total_expenses = sum(expenses_by_territory.values())
        avg_cps = total_expenses / total_samples if total_samples > 0 else Decimal('0')
        avg_collector_cost = total_collector_cost / len(result) if result else Decimal('0')
        avg_delta = avg_pps - avg_cps
        # Calculate total BPS (total placed revenue / total samples)
        total_placed_revenue = sum(Decimal(str(row[2])) for row in rows)  # row[2] is placed_revenue
        avg_bps = total_placed_revenue / total_samples if total_samples > 0 else Decimal('0')
        avg_collection_pct = (total_collection_weighted / total_collection_weight * 100) if total_collection_weight > 0 else 0
        
        # Create totals row
        totals = {
            'practice': 'TOTAL',
            'territory': '',
            'revenue': round(float(total_revenue), 2),
            'cogs': round(float(total_cogs), 2),
            'profit': round(float(total_profit), 2),
            'collection_pct': f"{round(avg_collection_pct, 1)}%",
            'revenue_periods': 0,
            'rps': round(float(avg_rps), 2),
            'bps': round(float(avg_bps), 2),
            'pps': round(float(avg_pps), 2),
            'cps': round(float(avg_cps), 2),
            'delta': round(float(avg_delta), 2),
            'collector': '',
            'collector_cost': round(float(avg_collector_cost), 2),
            'sample_count': total_samples
        }

        cursor.close()
        conn.close()

        return jsonify({
            'accounts': result, 
            'totals': totals,
            'period_type': period_type, 
            'count': len(result)
        }), 200
    except Exception as e:
        import traceback
        print('--- Exception in /account-table-live ---')
        traceback.print_exc()
        print('--- End Exception ---')
        return jsonify({'error': f'Failed to get live account table data: {str(e)}'}), 500

@dashboard_bp.route('/update-collector', methods=['POST'])
def update_collector():
    """Update the collector status for a practice."""
    try:
        data = request.get_json()
        practice = data.get('practice')
        collector = data.get('collector')
        if not practice or collector not in ['Y', 'N']:
            return jsonify({'error': 'Invalid input'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE account_data
            SET collector = %s
            WHERE practice_name = %s
        """, (collector, practice))
        if cursor.rowcount == 0:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': 'Practice not found'}), 404
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/update-collector-cost', methods=['POST'])
def update_collector_cost():
    """Update the collector cost for a practice."""
    try:
        data = request.get_json()
        practice = data.get('practice')
        collector_cost = data.get('collector_cost')
        
        if not practice or collector_cost is None:
            return jsonify({'error': 'Invalid input'}), 400
            
        # Convert to Decimal for precision
        from decimal import Decimal
        collector_cost = Decimal(str(collector_cost))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update collector cost in account_data table
        cursor.execute("""
            UPDATE account_data
            SET collector_cost = %s
            WHERE practice_name = %s
        """, (collector_cost, practice))
        
        if cursor.rowcount == 0:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({'error': 'Practice not found'}), 404
            
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 

def get_month_name_and_range(period_type, today=None):
    from datetime import datetime, timedelta
    import calendar
    if today is None:
        today = datetime.now()
    
    # Handle new month format (e.g., "june_2025")
    if '_' in period_type:
        try:
            month_str, year_str = period_type.split('_')
            year = int(year_str)
            
            # Convert month name to number
            month_names = [
                'january', 'february', 'march', 'april', 'may', 'june',
                'july', 'august', 'september', 'october', 'november', 'december'
            ]
            month_num = month_names.index(month_str.lower()) + 1
            
            start_date = datetime(year, month_num, 1)
            end_date = datetime(year, month_num, calendar.monthrange(year, month_num)[1])
            month_name = start_date.strftime('%B %Y')
            return month_name, start_date, end_date
        except (ValueError, IndexError):
            pass
    
    # Handle legacy period types
    if period_type == 'month':
        first_of_this_month = datetime(today.year, today.month, 1)
        last_month_end = first_of_this_month - timedelta(days=1)
        start_date = datetime(last_month_end.year, last_month_end.month, 1)
        end_date = datetime(last_month_end.year, last_month_end.month, calendar.monthrange(last_month_end.year, last_month_end.month)[1])
        month_name = start_date.strftime('%B %Y')
        return month_name, start_date, end_date
    elif period_type == 'ytd':
        start_date = datetime(today.year, 1, 1)
        end_date = today
        month_name = f"YTD {today.year}"
        return month_name, start_date, end_date
    # Add more period types as needed
    return None, None, None

@dashboard_bp.route('/financial-class-breakdown', methods=['GET'])
def financial_class_breakdown():
    """Return financial class breakdown for a practice and period, grouped by financial_class and summed by initial_balance."""
    try:
        practice = request.args.get('practice')
        period_type = request.args.get('period_type', 'month')
        if not practice:
            return jsonify({'error': 'Missing practice'}), 400
        month_name, start_date, end_date = get_month_name_and_range(period_type)
        if not start_date or not end_date:
            return jsonify({'error': 'Invalid period_type'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get all account numbers for the practice
        cursor.execute("""
            SELECT DISTINCT account_number FROM account_data WHERE practice_name = %s
        """, (practice,))
        account_numbers = [row[0] for row in cursor.fetchall()]
        print(f"[DEBUG] Practice: {practice}")
        print(f"[DEBUG] Account Numbers: {account_numbers}")
        print(f"[DEBUG] Start Date: {start_date}, End Date: {end_date}")
        if not account_numbers:
            cursor.close()
            conn.close()
            print("[DEBUG] No account numbers found for practice.")
            return jsonify({'period': month_name, 'breakdown': []})
        # Try both account_number and client_account_number in sample_billing
        # First, try account_number
        cursor.execute(f"""
            SELECT financial_class, SUM(initial_balance) as total_revenue
            FROM sample_billing
            WHERE account_number = ANY(%s)
              AND placement_date >= %s AND placement_date <= %s
            GROUP BY financial_class
        """, (account_numbers, start_date, end_date))
        rows = cursor.fetchall()
        print(f"[DEBUG] Rows returned using account_number: {len(rows)}")
        if not rows:
            # Try client_account_number if nothing found
            cursor.execute(f"""
                SELECT financial_class, SUM(initial_balance) as total_revenue
                FROM sample_billing
                WHERE client_account_number = ANY(%s)
                  AND placement_date >= %s AND placement_date <= %s
                GROUP BY financial_class
            """, (account_numbers, start_date, end_date))
            rows = cursor.fetchall()
            print(f"[DEBUG] Rows returned using client_account_number: {len(rows)}")
        cursor.close()
        conn.close()
        if not rows:
            print("[DEBUG] No rows found for either account_number or client_account_number.")
            return jsonify({'period': month_name, 'breakdown': []})
        total_revenue = sum(float(row[1]) for row in rows if row[1] is not None)
        breakdown = [
            {'class': row[0], 'revenue': float(row[1]), 'percent': round(100*float(row[1])/total_revenue, 1) if total_revenue else 0}
            for row in rows
        ]
        breakdown.sort(key=lambda x: -x['revenue'])
        print(f"[DEBUG] Breakdown: {breakdown}")
        return jsonify({'period': month_name, 'breakdown': breakdown})
    except Exception as e:
        print(f"[DEBUG] Exception: {e}")
        return jsonify({'error': str(e)}), 500 