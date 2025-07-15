#!/usr/bin/env python3
"""
QuickBooks Online Setup Script
Helps configure and test QBO integration.
"""

import os
import sys
from dotenv import load_dotenv

def check_environment():
    """Check if required environment variables are set."""
    load_dotenv()
    
    required_vars = [
        'QBO_CLIENT_ID',
        'QBO_CLIENT_SECRET',
        'QBO_ENVIRONMENT',
        'QBO_REDIRECT_URI'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables in your .env file")
        return False
    
    print("✅ All required QBO environment variables are set")
    return True

def test_qbo_service():
    """Test the QBO service initialization."""
    try:
        from app.services.qbo_service import QBOService
        qbo_service = QBOService()
        print("✅ QBO service initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize QBO service: {str(e)}")
        return False

def test_database_connection():
    """Test database connection."""
    try:
        import psycopg2
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def setup_database_schema():
    """Setup database schema for QBO integration."""
    try:
        import psycopg2
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        cursor = conn.cursor()
        
        # Read and execute the schema file
        with open('database/schemas/init.sql', 'r') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Database schema setup completed")
        return True
    except Exception as e:
        print(f"❌ Database schema setup failed: {str(e)}")
        return False

def main():
    """Main setup function."""
    print("🚀 QuickBooks Online Setup")
    print("=" * 40)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Test database connection
    if not test_database_connection():
        print("\nPlease ensure PostgreSQL is running and DATABASE_URL is correct")
        sys.exit(1)
    
    # Setup database schema
    if not setup_database_schema():
        sys.exit(1)
    
    # Test QBO service
    if not test_qbo_service():
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the Flask application: python app.py")
    print("2. Visit http://localhost:5000/auth")
    print("3. Login with demo credentials: admin / password123")
    print("4. Click 'Connect QuickBooks Online' to authenticate")
    print("5. Visit http://localhost:5000/dashboard to see real QBO data")

if __name__ == '__main__':
    main() 