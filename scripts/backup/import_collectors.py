#!/usr/bin/env python3
"""
Import Collectors data from Excel file into the database.
"""

import pandas as pd
import psycopg2
import os
import sys
from psycopg2.extras import execute_batch

# Database configuration
DB_CONFIG = {
    'db_name': os.getenv('DB_NAME', 'healthtech'),
    'db_user': os.getenv('DB_USER', 'postgres'),
    'db_password': os.getenv('DB_PASSWORD', 'OMT8459sl!'),
    'db_host': os.getenv('DB_HOST', 'localhost'),
    'db_port': os.getenv('DB_PORT', '5432')
}

def create_collectors_table(config):
    """Create the collectors table if it doesn't exist."""
    try:
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )
        cursor = conn.cursor()
        
        # Read and execute the SQL script
        sql_file = os.path.join(os.path.dirname(__file__), 'create_collectors_table.sql')
        with open(sql_file, 'r') as f:
            sql_script = f.read()
        
        cursor.execute(sql_script)
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Collectors table created successfully!")
        
    except Exception as e:
        print(f"Error creating table: {e}")
        sys.exit(1)

def import_excel_data(config):
    """Import data from Excel file into the database."""
    try:
        # Read Excel file
        excel_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'Data',
            'Collectors.xlsx'
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
        
        # Clean data: handle NaN values
        df = df.fillna(0)
        
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
        cursor.execute("DELETE FROM collectors")
        print("Cleared existing data from collectors table")
        
        # Prepare data for batch insert
        data_to_insert = []
        for index, row in df.iterrows():
            data_to_insert.append((
                row['Territory'],
                row['Practice'],
                row['Collector'],
                float(row['March']) if pd.notna(row['March']) else 0.0,
                float(row['April']) if pd.notna(row['April']) else 0.0,
                float(row['May']) if pd.notna(row['May']) else 0.0,
                float(row['June']) if pd.notna(row['June']) else 0.0
            ))
        
        # Batch insert
        print("Inserting data...")
        execute_batch(cursor, """
            INSERT INTO collectors (territory, practice, collector, march_amount, april_amount, may_amount, june_amount)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, data_to_insert, page_size=100)
        
        conn.commit()
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM collectors")
        count = cursor.fetchone()[0]
        print(f"\nImport Summary:")
        print(f"Successfully imported: {count} records")
        
        # Show sample of imported data
        cursor.execute("SELECT * FROM collectors LIMIT 5")
        sample_data = cursor.fetchall()
        print("\nSample imported data:")
        for row in sample_data:
            print(f"  {row}")
        
        # Show territory distribution
        cursor.execute("SELECT territory, COUNT(*) FROM collectors GROUP BY territory ORDER BY COUNT(*) DESC")
        territory_data = cursor.fetchall()
        print("\nTerritory distribution:")
        for territory, count in territory_data:
            print(f"  {territory}: {count} records")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error importing data: {e}")
        sys.exit(1)

def main():
    """Main function to run the import process."""
    print("Starting Collectors data import...")
    
    # Create table
    create_collectors_table(DB_CONFIG)
    
    # Import data
    import_excel_data(DB_CONFIG)
    
    print("Collectors data import completed successfully!")

if __name__ == "__main__":
    main()

    # Print the number of unique collectors
    try:
        conn = psycopg2.connect(
            host=DB_CONFIG['db_host'],
            port=DB_CONFIG['db_port'],
            user=DB_CONFIG['db_user'],
            password=DB_CONFIG['db_password'],
            database=DB_CONFIG['db_name']
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(DISTINCT collector) FROM collectors;")
        count = cur.fetchone()[0]
        print(f"\nNumber of unique collectors in the table: {count}")
        cur.execute("SELECT DISTINCT collector FROM collectors ORDER BY collector;")
        names = [row[0] for row in cur.fetchall()]
        print("Collector names:")
        for name in names:
            print(f"  - {name}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error counting unique collectors: {e}") 