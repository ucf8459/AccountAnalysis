#!/usr/bin/env python3
"""
Run SQL script using database connection from .env file.
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_sql_script(script_path):
    """Run SQL script using database connection from .env."""
    try:
        # Get database connection from .env
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL not found in .env file")
        
        print(f"Connecting to database using DATABASE_URL")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Read and execute SQL script
        with open(script_path, 'r') as f:
            sql_script = f.read()
        
        print(f"Executing SQL script: {script_path}")
        cursor.execute(sql_script)
        conn.commit()
        
        print("SQL script executed successfully!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error executing SQL script: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
        run_sql_script(script_path)
    else:
        print("Usage: python run_sql_script.py <script_path>") 