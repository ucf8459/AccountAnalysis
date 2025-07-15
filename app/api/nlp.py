"""
NLP API endpoints for natural language query processing using OpenAI.
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import psycopg2
import os
import openai
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

nlp_bp = Blueprint('nlp', __name__)

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def get_database_schema():
    """Get database schema information for SQL generation."""
    return """
    Database Schema for Account Analysis:
    
    -- Raw Tables
    raw.qbo_transactions (
        id, qbo_id, customer_name, account_name, amount, txn_date, txn_type, description, raw_json
    )
    
    -- Staging Tables
    staging.transactions_cleaned (
        id, qbo_id, customer_id, account_id, amount, txn_date, region, territory, sales_rep, product_category
    )
    
    staging.external_data_cleaned (
        id, source_name, metric_name, metric_value, metric_date, account_id, territory
    )
    
    -- Analytics Tables
    analytics.financial_summary (
        id, customer_id, account_id, total_revenue, total_cogs, total_expenses, gross_profit, net_profit, 
        period_start, period_end, region, territory
    )
    
    analytics.territory_performance (
        id, territory_name, total_sales, num_accounts, avg_revenue_per_account, report_date, period_type
    )
    
    analytics.account_kpis (
        id, account_id, account_name, revenue_per_sample, cost_of_sale, billing_per_sample, 
        collection_rate, territory, report_date
    )
    
    -- Authentication Tables
    auth.users (id, username, email, password_hash, role, is_active, created_at, updated_at)
    auth.user_sessions (id, user_id, session_token, expires_at, created_at)
    """

def generate_sql_from_question(question):
    """Generate SQL query from natural language question using OpenAI."""
    try:
        schema_info = get_database_schema()
        
        prompt = f"""
        You are a SQL expert for a financial analytics database. 
        Based on the following database schema, generate a PostgreSQL query to answer the user's question.
        
        Database Schema:
        {schema_info}
        
        User Question: {question}
        
        Instructions:
        1. Generate only the SQL query, no explanations
        2. Use appropriate table joins when needed
        3. Include proper WHERE clauses for filtering
        4. Use appropriate aggregation functions (SUM, COUNT, AVG, etc.)
        5. Order results logically
        6. Limit results to 100 rows if no specific limit is mentioned
        7. Use proper date formatting and comparisons
        
        SQL Query:
        """
        
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a SQL expert. Generate only SQL queries, no explanations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up the SQL query
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
        
    except Exception as e:
        raise Exception(f"Failed to generate SQL: {str(e)}")

def execute_sql_query(sql_query):
    """Execute SQL query and return results."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(sql_query)
        results = cursor.fetchall()
        
        # Get column names
        column_names = [desc[0] for desc in cursor.description]
        
        # Convert results to list of dictionaries
        data = []
        for row in results:
            row_dict = {}
            for i, value in enumerate(row):
                if isinstance(value, datetime):
                    row_dict[column_names[i]] = value.isoformat()
                elif isinstance(value, (int, float)):
                    row_dict[column_names[i]] = value
                else:
                    row_dict[column_names[i]] = str(value) if value is not None else None
            data.append(row_dict)
        
        cursor.close()
        conn.close()
        
        return {
            'columns': column_names,
            'data': data,
            'row_count': len(data)
        }
        
    except Exception as e:
        raise Exception(f"Failed to execute SQL query: {str(e)}")

@nlp_bp.route('/query', methods=['POST'])
@jwt_required()
def process_natural_language_query():
    """Process natural language query and return results."""
    try:
        data = request.get_json()
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        # Generate SQL from question
        sql_query = generate_sql_from_question(question)
        
        # Execute the SQL query
        results = execute_sql_query(sql_query)
        
        # Log the query for audit purposes
        current_user_id = get_jwt_identity()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO staging.data_quality_log (table_name, check_type, records_processed, error_details)
            VALUES (%s, %s, %s, %s)
        """, ('nlp_query', 'natural_language_query', results['row_count'], 
              {'question': question, 'sql_query': sql_query, 'user_id': current_user_id}))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'question': question,
            'sql_query': sql_query,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to process query: {str(e)}'}), 500

@nlp_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def get_query_suggestions():
    """Get suggested questions for users."""
    suggestions = [
        "What is the total revenue for the last 30 days?",
        "Which territory has the highest sales?",
        "Show me accounts with revenue per sample above $100",
        "What is the average collection rate by territory?",
        "How many accounts do we have in each region?",
        "Show me the top 10 accounts by revenue",
        "What is the gross profit margin by territory?",
        "Which accounts have collection rates below 80%?",
        "Show me monthly revenue trends for the last 6 months",
        "What is the cost of sale distribution by product category?"
    ]
    
    return jsonify({
        'suggestions': suggestions
    }), 200

@nlp_bp.route('/history', methods=['GET'])
@jwt_required()
def get_query_history():
    """Get user's query history."""
    try:
        current_user_id = get_jwt_identity()
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                check_date,
                error_details->>'question' as question,
                error_details->>'sql_query' as sql_query,
                records_processed as result_count
            FROM staging.data_quality_log
            WHERE check_type = 'natural_language_query'
            AND error_details->>'user_id' = %s
            ORDER BY check_date DESC
            LIMIT 20
        """, (str(current_user_id),))
        
        results = cursor.fetchall()
        
        query_history = []
        for row in results:
            query_history.append({
                'timestamp': row[0].isoformat() if row[0] else None,
                'question': row[1],
                'sql_query': row[2],
                'result_count': row[3]
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'query_history': query_history,
            'count': len(query_history)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get query history: {str(e)}'}), 500

@nlp_bp.route('/validate', methods=['POST'])
@jwt_required()
def validate_sql_query():
    """Validate a SQL query without executing it."""
    try:
        data = request.get_json()
        sql_query = data.get('sql_query')
        
        if not sql_query:
            return jsonify({'error': 'SQL query is required'}), 400
        
        # Basic SQL validation
        sql_lower = sql_query.lower()
        
        # Check for potentially dangerous operations
        dangerous_keywords = ['drop', 'delete', 'truncate', 'alter', 'create', 'insert', 'update']
        for keyword in dangerous_keywords:
            if keyword in sql_lower:
                return jsonify({
                    'valid': False,
                    'error': f'Query contains potentially dangerous keyword: {keyword}'
                }), 400
        
        # Check if it's a SELECT query
        if not sql_lower.strip().startswith('select'):
            return jsonify({
                'valid': False,
                'error': 'Only SELECT queries are allowed'
            }), 400
        
        # Try to parse the query (basic validation)
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Use EXPLAIN to validate the query without executing it
            cursor.execute(f"EXPLAIN {sql_query}")
            explain_result = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'valid': True,
                'message': 'SQL query is valid',
                'explain_plan': [row[0] for row in explain_result]
            }), 200
            
        except Exception as parse_error:
            return jsonify({
                'valid': False,
                'error': f'SQL syntax error: {str(parse_error)}'
            }), 400
        
    except Exception as e:
        return jsonify({'error': f'Failed to validate query: {str(e)}'}), 500 