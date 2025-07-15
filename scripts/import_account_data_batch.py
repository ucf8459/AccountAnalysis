#!/usr/bin/env python3
"""
Import account data from Excel file into healthtech database using batch processing.
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import sys
from psycopg2.extras import execute_batch

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
        
        # Drop table if exists and recreate
        cursor.execute("DROP TABLE IF EXISTS account_data")
        
        # Create account_data table
        cursor.execute("""
            CREATE TABLE account_data (
                id SERIAL PRIMARY KEY,
                practice_name VARCHAR(255),
                account_number VARCHAR(255) UNIQUE NOT NULL,
                sales_rep VARCHAR(255),
                territory VARCHAR(255),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX idx_account_data_practice ON account_data(practice_name)")
        cursor.execute("CREATE INDEX idx_account_data_territory ON account_data(territory)")
        cursor.execute("CREATE INDEX idx_account_data_sales_rep ON account_data(sales_rep)")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Account data table created successfully!")
        
    except Exception as e:
        print(f"Error creating table: {e}")
        sys.exit(1)

def import_excel_data_batch(config):
    """Import data from Excel file into the database using batch processing."""
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
        
        print(f"Found {len(df)} records before cleaning")
        print("Columns:", df.columns.tolist())
        print("Sample data:")
        print(df.head())
        
        # Clean data: drop rows with missing account numbers, keep only first occurrence of each account number
        df = df.dropna(subset=['Account Number'])
        df = df[df['Account Number'].astype(str).str.strip() != '']
        df = df.drop_duplicates(subset=['Account Number'], keep='first')
        print(f"{len(df)} records after dropping missing/duplicate account numbers")
        
        # Connect to database
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )
        cursor = conn.cursor()
        
        # Prepare data for batch insert
        data_to_insert = []
        for index, row in df.iterrows():
            data_to_insert.append((
                row['Practice Name'],
                row['Account Number'],
                row['Sales Rep'],
                row['Territory']
            ))
        
        # Batch insert
        print("Inserting data in batches...")
        batch_size = 1000
        total_inserted = 0
        errors = 0
        
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i:i + batch_size]
            try:
                execute_batch(cursor, """
                    INSERT INTO account_data (practice_name, account_number, sales_rep, territory)
                    VALUES (%s, %s, %s, %s)
                """, batch, page_size=100)
                conn.commit()
                total_inserted += len(batch)
                print(f"Inserted batch {i//batch_size + 1}: {len(batch)} records (Total: {total_inserted})")
            except Exception as e:
                print(f"Error in batch {i//batch_size + 1}: {e}")
                conn.rollback()
                errors += 1
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM account_data")
        count = cursor.fetchone()[0]
        print(f"\nImport Summary:")
        print(f"Successfully imported: {count} records")
        print(f"Errors encountered: {errors}")
        
        # Show sample of imported data
        cursor.execute("SELECT * FROM account_data LIMIT 5")
        sample_data = cursor.fetchall()
        print("\nSample imported data:")
        for row in sample_data:
            print(f"  {row}")
        
        # Show territory distribution
        cursor.execute("SELECT territory, COUNT(*) FROM account_data GROUP BY territory ORDER BY COUNT(*) DESC")
        territory_data = cursor.fetchall()
        print("\nTerritory distribution:")
        for territory, count in territory_data:
            print(f"  {territory}: {count} accounts")
        
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
    import_excel_data_batch(config)
    
    print("\nAccount data import completed successfully!")

if __name__ == "__main__":
    main() 