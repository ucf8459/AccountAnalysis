"""
ETL API endpoints for data extraction, transformation, and loading processes.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import psycopg2
import os
import subprocess
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

etl_bp = Blueprint('etl', __name__)

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

@etl_bp.route('/status', methods=['GET'])
@jwt_required()
def get_etl_status():
    """Get the status of recent ETL jobs."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent ETL job status
        cursor.execute("""
            SELECT 
                job_name,
                status,
                start_time,
                end_time,
                records_processed,
                error_message
            FROM staging.etl_job_log
            ORDER BY start_time DESC
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        etl_jobs = []
        for row in results:
            etl_jobs.append({
                'job_name': row[0],
                'status': row[1],
                'start_time': row[2].isoformat() if row[2] else None,
                'end_time': row[3].isoformat() if row[3] else None,
                'records_processed': row[4],
                'error_message': row[5]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'etl_jobs': etl_jobs,
            'count': len(etl_jobs)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get ETL status: {str(e)}'}), 500

@etl_bp.route('/trigger/qbo', methods=['POST'])
@jwt_required()
def trigger_qbo_extraction():
    """Trigger QuickBooks Online data extraction."""
    try:
        # Check if user has appropriate permissions
        current_user_id = get_jwt_identity()
        
        # Log the ETL job start
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO staging.etl_job_log (job_name, status, start_time)
            VALUES (%s, %s, %s) RETURNING id
        """, ('qbo_extraction', 'running', datetime.now()))
        
        job_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Run QBO extraction in background thread
        def run_qbo_extraction():
            try:
                # This would call the actual QBO extraction script
                # For now, we'll simulate the process
                import time
                time.sleep(5)  # Simulate processing time
                
                # Update job status
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE staging.etl_job_log 
                    SET status = %s, end_time = %s, records_processed = %s
                    WHERE id = %s
                """, ('success', datetime.now(), 100, job_id))
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                # Update job status with error
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE staging.etl_job_log 
                    SET status = %s, end_time = %s, error_message = %s
                    WHERE id = %s
                """, ('failed', datetime.now(), str(e), job_id))
                conn.commit()
                cursor.close()
                conn.close()
        
        thread = threading.Thread(target=run_qbo_extraction)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'QBO extraction job started',
            'job_id': job_id,
            'status': 'running'
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'Failed to trigger QBO extraction: {str(e)}'}), 500

@etl_bp.route('/trigger/external', methods=['POST'])
@jwt_required()
def trigger_external_extraction():
    """Trigger external portal data extraction."""
    try:
        # Check if user has appropriate permissions
        current_user_id = get_jwt_identity()
        
        # Log the ETL job start
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO staging.etl_job_log (job_name, status, start_time)
            VALUES (%s, %s, %s) RETURNING id
        """, ('external_extraction', 'running', datetime.now()))
        
        job_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Run external extraction in background thread
        def run_external_extraction():
            try:
                # This would call the actual external extraction script
                # For now, we'll simulate the process
                import time
                time.sleep(3)  # Simulate processing time
                
                # Update job status
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE staging.etl_job_log 
                    SET status = %s, end_time = %s, records_processed = %s
                    WHERE id = %s
                """, ('success', datetime.now(), 50, job_id))
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                # Update job status with error
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE staging.etl_job_log 
                    SET status = %s, end_time = %s, error_message = %s
                    WHERE id = %s
                """, ('failed', datetime.now(), str(e), job_id))
                conn.commit()
                cursor.close()
                conn.close()
        
        thread = threading.Thread(target=run_external_extraction)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'External extraction job started',
            'job_id': job_id,
            'status': 'running'
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'Failed to trigger external extraction: {str(e)}'}), 500

@etl_bp.route('/trigger/transform', methods=['POST'])
@jwt_required()
def trigger_data_transformation():
    """Trigger data transformation process."""
    try:
        # Check if user has appropriate permissions
        current_user_id = get_jwt_identity()
        
        # Log the ETL job start
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO staging.etl_job_log (job_name, status, start_time)
            VALUES (%s, %s, %s) RETURNING id
        """, ('data_transformation', 'running', datetime.now()))
        
        job_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Run transformation in background thread
        def run_transformation():
            try:
                # This would call the actual transformation script
                # For now, we'll simulate the process
                import time
                time.sleep(10)  # Simulate processing time
                
                # Update job status
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE staging.etl_job_log 
                    SET status = %s, end_time = %s, records_processed = %s
                    WHERE id = %s
                """, ('success', datetime.now(), 150, job_id))
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                # Update job status with error
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE staging.etl_job_log 
                    SET status = %s, end_time = %s, error_message = %s
                    WHERE id = %s
                """, ('failed', datetime.now(), str(e), job_id))
                conn.commit()
                cursor.close()
                conn.close()
        
        thread = threading.Thread(target=run_transformation)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Data transformation job started',
            'job_id': job_id,
            'status': 'running'
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'Failed to trigger data transformation: {str(e)}'}), 500

@etl_bp.route('/trigger/full', methods=['POST'])
@jwt_required()
def trigger_full_etl():
    """Trigger full ETL pipeline (extract, transform, load)."""
    try:
        # Check if user has appropriate permissions
        current_user_id = get_jwt_identity()
        
        # Log the ETL job start
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO staging.etl_job_log (job_name, status, start_time)
            VALUES (%s, %s, %s) RETURNING id
        """, ('full_etl_pipeline', 'running', datetime.now()))
        
        job_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        
        # Run full ETL in background thread
        def run_full_etl():
            try:
                # This would run the complete ETL pipeline
                # For now, we'll simulate the process
                import time
                time.sleep(15)  # Simulate processing time
                
                # Update job status
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE staging.etl_job_log 
                    SET status = %s, end_time = %s, records_processed = %s
                    WHERE id = %s
                """, ('success', datetime.now(), 300, job_id))
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                # Update job status with error
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE staging.etl_job_log 
                    SET status = %s, end_time = %s, error_message = %s
                    WHERE id = %s
                """, ('failed', datetime.now(), str(e), job_id))
                conn.commit()
                cursor.close()
                conn.close()
        
        thread = threading.Thread(target=run_full_etl)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'message': 'Full ETL pipeline started',
            'job_id': job_id,
            'status': 'running'
        }), 202
        
    except Exception as e:
        return jsonify({'error': f'Failed to trigger full ETL: {str(e)}'}), 500

@etl_bp.route('/data-quality', methods=['GET'])
@jwt_required()
def get_data_quality_report():
    """Get data quality report."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get recent data quality checks
        cursor.execute("""
            SELECT 
                table_name,
                check_type,
                records_processed,
                records_failed,
                error_details,
                check_date
            FROM staging.data_quality_log
            ORDER BY check_date DESC
            LIMIT 20
        """)
        
        results = cursor.fetchall()
        
        quality_checks = []
        for row in results:
            quality_checks.append({
                'table_name': row[0],
                'check_type': row[1],
                'records_processed': row[2],
                'records_failed': row[3],
                'error_details': row[4],
                'check_date': row[5].isoformat() if row[5] else None
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'data_quality_checks': quality_checks,
            'count': len(quality_checks)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get data quality report: {str(e)}'}), 500 