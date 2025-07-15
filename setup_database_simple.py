#!/usr/bin/env python3
"""
Simple database setup script for development.
This script will help you set up the database with common configurations.
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def test_connection(host, port, user, password, database='postgres'):
    """Test database connection."""
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        conn.close()
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False

def create_database(host, port, user, password, db_name):
    """Create the database if it doesn't exist."""
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database: {db_name}")
            cursor.execute(f"CREATE DATABASE {db_name}")
            print(f"Database {db_name} created successfully!")
        else:
            print(f"Database {db_name} already exists.")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def main():
    """Main setup function."""
    print("Account Analysis Database Setup")
    print("=" * 40)
    
    # Common PostgreSQL configurations to try
    configs = [
        {
            'name': 'Default PostgreSQL (password: postgres)',
            'host': 'localhost',
            'port': '5432',
            'user': 'postgres',
            'password': 'postgres'
        },
        {
            'name': 'Default PostgreSQL (no password)',
            'host': 'localhost',
            'port': '5432',
            'user': 'postgres',
            'password': ''
        },
        {
            'name': 'Default PostgreSQL (password: admin)',
            'host': 'localhost',
            'port': '5432',
            'user': 'postgres',
            'password': 'admin'
        }
    ]
    
    db_name = 'account_analysis'
    
    print("Testing common PostgreSQL configurations...")
    
    working_config = None
    for config in configs:
        print(f"\nTrying: {config['name']}")
        if test_connection(config['host'], config['port'], config['user'], config['password']):
            print("✓ Connection successful!")
            working_config = config
            break
        else:
            print("✗ Connection failed")
    
    if not working_config:
        print("\nNone of the common configurations worked.")
        print("\nPlease manually configure your database:")
        print("1. Make sure PostgreSQL is running")
        print("2. Update your .env file with the correct credentials:")
        print("   DB_HOST=localhost")
        print("   DB_PORT=5432")
        print("   DB_NAME=account_analysis")
        print("   DB_USER=your_username")
        print("   DB_PASSWORD=your_password")
        return
    
    print(f"\nUsing configuration: {working_config['name']}")
    
    # Create the database
    if create_database(working_config['host'], working_config['port'], 
                      working_config['user'], working_config['password'], db_name):
        
        print(f"\nDatabase setup successful!")
        print(f"\nUpdate your .env file with these settings:")
        print(f"DB_HOST={working_config['host']}")
        print(f"DB_PORT={working_config['port']}")
        print(f"DB_NAME={db_name}")
        print(f"DB_USER={working_config['user']}")
        print(f"DB_PASSWORD={working_config['password']}")
        
        # Update .env file
        env_content = f"""# Database Configuration
DATABASE_URL=postgresql://{working_config['user']}:{working_config['password']}@{working_config['host']}:{working_config['port']}/{db_name}
DB_HOST={working_config['host']}
DB_PORT={working_config['port']}
DB_NAME={db_name}
DB_USER={working_config['user']}
DB_PASSWORD={working_config['password']}

# QuickBooks Online API
QBO_CLIENT_ID=your_qbo_client_id
QBO_CLIENT_SECRET=your_qbo_client_secret
QBO_ENVIRONMENT=sandbox  # or production
QBO_REDIRECT_URI=http://localhost:5000/auth/qbo/callback

# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo

# JWT Authentication
JWT_SECRET_KEY=your_super_secret_jwt_key_change_this_in_production
JWT_ACCESS_TOKEN_EXPIRES=3600  # 1 hour

# External Portal Credentials (for headless browser)
EXTERNAL_PORTAL_URL=https://your-external-portal.com
EXTERNAL_PORTAL_USERNAME=your_username
EXTERNAL_PORTAL_PASSWORD=your_password

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_SECRET_KEY=your_flask_secret_key
PORT=5000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Monitoring
SENTRY_DSN=your_sentry_dsn  # Optional for error tracking

# ETL Settings
ETL_BATCH_SIZE=1000
ETL_MAX_RETRIES=3
ETL_RETRY_DELAY=300  # seconds

# File Storage
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print(f"\n.env file updated successfully!")
        print(f"\nNext steps:")
        print(f"1. Run: python scripts/setup_database.py")
        print(f"2. Run: python app.py")
        
    else:
        print("Failed to create database. Please check your PostgreSQL installation.")

if __name__ == "__main__":
    main() 