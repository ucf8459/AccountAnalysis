#!/usr/bin/env python3
"""
Database setup script for Account Analysis application.
Creates the database, schemas, and initial tables.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    
    return {
        'db_host': os.getenv('DB_HOST', 'localhost'),
        'db_port': os.getenv('DB_PORT', '5432'),
        'db_name': os.getenv('DB_NAME', 'account_analysis'),
        'db_user': os.getenv('DB_USER', 'postgres'),
        'db_password': os.getenv('DB_PASSWORD', ''),
    }

def create_database(config):
    """Create the database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (config['db_name'],))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database: {config['db_name']}")
            cursor.execute(f"CREATE DATABASE {config['db_name']}")
            print(f"Database {config['db_name']} created successfully!")
        else:
            print(f"Database {config['db_name']} already exists.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

def setup_schema(config):
    """Set up the database schema and tables."""
    try:
        # Connect to the specific database
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )
        cursor = conn.cursor()
        
        # Read and execute the schema file
        schema_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'database', 'schemas', 'init.sql'
        )
        
        if os.path.exists(schema_file):
            print("Setting up database schema...")
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            # Split by semicolon and execute each statement
            statements = schema_sql.split(';')
            for statement in statements:
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            
            conn.commit()
            print("Database schema set up successfully!")
        else:
            print(f"Schema file not found: {schema_file}")
            sys.exit(1)
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error setting up schema: {e}")
        sys.exit(1)

def verify_setup(config):
    """Verify that the setup was successful."""
    try:
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )
        cursor = conn.cursor()
        
        # Check if schemas exist
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name IN ('raw', 'staging', 'analytics', 'auth')
        """)
        schemas = [row[0] for row in cursor.fetchall()]
        
        print(f"Found schemas: {schemas}")
        
        # Check if key tables exist
        cursor.execute("""
            SELECT table_name, table_schema 
            FROM information_schema.tables 
            WHERE table_schema IN ('raw', 'staging', 'analytics', 'auth')
            ORDER BY table_schema, table_name
        """)
        tables = cursor.fetchall()
        
        print("Created tables:")
        for table in tables:
            print(f"  {table[1]}.{table[0]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error verifying setup: {e}")
        sys.exit(1)

def main():
    """Main setup function."""
    print("Setting up Account Analysis database...")
    
    # Load configuration
    config = load_config()
    print(f"Using database: {config['db_name']} on {config['db_host']}:{config['db_port']}")
    
    # Create database
    create_database(config)
    
    # Setup schema
    setup_schema(config)
    
    # Verify setup
    verify_setup(config)
    
    print("\nDatabase setup completed successfully!")
    print("\nNext steps:")
    print("1. Copy env.example to .env and configure your credentials")
    print("2. Install Python dependencies: pip install -r requirements.txt")
    print("3. Install Node.js dependencies: npm install")
    print("4. Run the application: python app.py")

if __name__ == "__main__":
    main() 