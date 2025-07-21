#!/usr/bin/env python3
"""
Import account data from Excel file into healthtech database.
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_config():
    """Load configuration from environment variables."""
    load_dotenv()
    
    return {
        'db_host': os.getenv('DB_HOST', 'localhost'),
        'db_port': os.getenv('DB_PORT', '5432'),
        'db_name': 'healthtech',  # Use healthtech database
        'db_user': os.getenv('DB_USER', 'postgres'),
        'db_password': 'OMT8459sl!',  # Use the provided password
    }

def create_account_table(config):
    """Create the account_data table if it doesn't exist."""
    try:
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )
        cursor = conn.cursor()
        
        # Create account_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_data (
                id SERIAL PRIMARY KEY,
                practice_name VARCHAR(255),
                account_number VARCHAR(255) UNIQUE NOT NULL,
                sales_rep VARCHAR(255),
                territory VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_account_data_practice ON account_data(practice_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_account_data_territory ON account_data(territory)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_account_data_sales_rep ON account_data(sales_rep)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Account data table created successfully!")
        
    except Exception as e:
        print(f"Error creating table: {e}")
        sys.exit(1)

def import_excel_data(config):
    """Import data from Excel file into the database."""
    try:
        # Read Excel file
        excel_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'Accounts through 0625.xlsx'
        )
        
        if not os.path.exists(excel_file):
            print(f"Excel file not found: {excel_file}")
            sys.exit(1)
        
        print(f"Reading Excel file: {excel_file}")
        df = pd.read_excel(excel_file)
        
        print(f"Found {len(df)} records")
        print("Columns:", df.columns.tolist())
        print("Sample data:")
        print(df.head())
        
        # Connect to database
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute("DELETE FROM account_data")
        print("Cleared existing data from account_data table")
        
        # Insert data
        print("Inserting data...")
        for index, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO account_data (practice_name, account_number, sales_rep, territory)
                    VALUES (%s, %s, %s, %s)
                """, (
                    row['Practice Name'],
                    row['Account Number'],
                    row['Sales Rep'],
                    row['Territory']
                ))
            except psycopg2.IntegrityError as e:
                print(f"Duplicate account number skipped: {row['Account Number']}")
            except Exception as e:
                print(f"Error inserting row {index}: {e}")
        
        conn.commit()
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM account_data")
        count = cursor.fetchone()[0]
        print(f"Successfully imported {count} records")
        
        # Show sample of imported data
        cursor.execute("SELECT * FROM account_data LIMIT 5")
        sample_data = cursor.fetchall()
        print("Sample imported data:")
        for row in sample_data:
            print(f"  {row}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error importing data: {e}")
        sys.exit(1)

def main():
    """Main import function."""
    print("Importing account data from Excel file...")
    
    # Load configuration
    config = load_config()
    print(f"Using database: {config['db_name']} on {config['db_host']}:{config['db_port']}")
    
    # Create table
    create_account_table(config)
    
    # Import data
    import_excel_data(config)
    
    print("\nAccount data import completed successfully!")

if __name__ == "__main__":
    main() 