#!/usr/bin/env python3
"""
Account Territory Mapping Import Script
Imports account number to sales rep/territory mapping data into the database.
"""

import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import argparse
from datetime import datetime

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

def read_mapping_file(file_path, file_type=None):
    """
    Read mapping data from file.
    Supports CSV and Excel files.
    """
    try:
        if file_type == 'csv' or file_path.lower().endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_type == 'excel' or file_path.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_path)
        else:
            # Try to auto-detect
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        
        print(f"Successfully read {len(df)} rows from {file_path}")
        print(f"Columns found: {list(df.columns)}")
        
        return df
        
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)

def validate_data(df):
    """
    Validate the mapping data and provide column mapping suggestions.
    """
    print("\n=== Data Validation ===")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Look for potential account number columns
    account_cols = [col for col in df.columns if any(keyword in col.lower() 
                   for keyword in ['account', 'client', 'sample', 'number', 'id'])]
    
    # Look for potential rep columns
    rep_cols = [col for col in df.columns if any(keyword in col.lower() 
              for keyword in ['rep', 'representative', 'sales', 'name'])]
    
    # Look for potential territory columns
    territory_cols = [col for col in df.columns if any(keyword in col.lower() 
                      for keyword in ['territory', 'region', 'area'])]
    
    print(f"\nPotential account number columns: {account_cols}")
    print(f"Potential sales rep columns: {rep_cols}")
    print(f"Potential territory columns: {territory_cols}")
    
    # Check for missing values
    print("\nMissing values per column:")
    for col in df.columns:
        missing = df[col].isnull().sum()
        if missing > 0:
            print(f"  {col}: {missing} missing values")
    
    return df

def map_columns(df, account_col=None, rep_col=None, territory_col=None, region_col=None):
    """
    Map the dataframe columns to the expected database columns.
    """
    if account_col and account_col not in df.columns:
        print(f"Error: Account column '{account_col}' not found in data")
        sys.exit(1)
    
    if rep_col and rep_col not in df.columns:
        print(f"Error: Sales rep column '{rep_col}' not found in data")
        sys.exit(1)
    
    if territory_col and territory_col not in df.columns:
        print(f"Error: Territory column '{territory_col}' not found in data")
        sys.exit(1)
    
    if region_col and region_col not in df.columns:
        print(f"Error: Region column '{region_col}' not found in data")
        sys.exit(1)
    
    # Create mapped dataframe
    mapped_df = pd.DataFrame()
    
    # Map account number (required)
    if account_col:
        mapped_df['account_number'] = df[account_col].astype(str).str.strip()
    else:
        print("Error: Account number column is required")
        sys.exit(1)
    
    # Map sales rep (optional)
    if rep_col:
        mapped_df['sales_rep_name'] = df[rep_col].astype(str).str.strip()
    else:
        mapped_df['sales_rep_name'] = None
    
    # Map territory (optional)
    if territory_col:
        mapped_df['territory_name'] = df[territory_col].astype(str).str.strip()
    else:
        mapped_df['territory_name'] = None
    
    # Map region (optional)
    if region_col:
        mapped_df['region'] = df[region_col].astype(str).str.strip()
    else:
        mapped_df['region'] = None
    
    # Add default values
    mapped_df['sales_rep_id'] = None
    mapped_df['territory_id'] = None
    mapped_df['is_active'] = True
    mapped_df['effective_date'] = datetime.now().date()
    mapped_df['end_date'] = None
    
    # Remove rows where account_number is empty or null
    initial_count = len(mapped_df)
    mapped_df = mapped_df.dropna(subset=['account_number'])
    mapped_df = mapped_df[mapped_df['account_number'] != '']
    mapped_df = mapped_df[mapped_df['account_number'] != 'nan']
    
    if len(mapped_df) < initial_count:
        print(f"Removed {initial_count - len(mapped_df)} rows with empty account numbers")
    
    return mapped_df

def import_to_database(config, df, dry_run=False):
    """
    Import the mapped data into the database.
    """
    try:
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )
        cursor = conn.cursor()
        
        if dry_run:
            print(f"\n=== DRY RUN - Would import {len(df)} rows ===")
            print("Sample data:")
            print(df.head().to_string())
            return
        
        # Check for existing records
        account_numbers = tuple(df['account_number'].tolist())
        if len(account_numbers) == 1:
            account_numbers = f"('{account_numbers[0]}')"
        
        cursor.execute(f"""
            SELECT account_number FROM staging.account_territory_mapping 
            WHERE account_number IN {account_numbers}
        """)
        existing_accounts = [row[0] for row in cursor.fetchall()]
        
        if existing_accounts:
            print(f"\nWarning: {len(existing_accounts)} account numbers already exist in database:")
            print(f"Existing accounts: {existing_accounts[:10]}{'...' if len(existing_accounts) > 10 else ''}")
            
            response = input("\nDo you want to update existing records? (y/n): ").lower()
            if response == 'y':
                # Update existing records
                for _, row in df.iterrows():
                    cursor.execute("""
                        UPDATE staging.account_territory_mapping 
                        SET sales_rep_name = %s, sales_rep_id = %s, territory_name = %s, 
                            territory_id = %s, region = %s, updated_at = NOW()
                        WHERE account_number = %s
                    """, (
                        row['sales_rep_name'], row['sales_rep_id'], row['territory_name'],
                        row['territory_id'], row['region'], row['account_number']
                    ))
                
                # Insert new records
                new_df = df[~df['account_number'].isin(existing_accounts)]
                if len(new_df) > 0:
                    insert_records(cursor, new_df)
            else:
                # Only insert new records
                new_df = df[~df['account_number'].isin(existing_accounts)]
                if len(new_df) > 0:
                    insert_records(cursor, new_df)
                else:
                    print("No new records to insert.")
        else:
            # Insert all records
            insert_records(cursor, df)
        
        conn.commit()
        print(f"\nSuccessfully imported {len(df)} account mappings!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error importing to database: {e}")
        sys.exit(1)

def insert_records(cursor, df):
    """Insert records into the database."""
    # Prepare data for bulk insert
    data = []
    for _, row in df.iterrows():
        data.append((
            row['account_number'],
            row['sales_rep_name'],
            row['sales_rep_id'],
            row['territory_name'],
            row['territory_id'],
            row['region'],
            row['is_active'],
            row['effective_date'],
            row['end_date']
        ))
    
    # Bulk insert
    execute_values(
        cursor,
        """
        INSERT INTO staging.account_territory_mapping 
        (account_number, sales_rep_name, sales_rep_id, territory_name, territory_id, 
         region, is_active, effective_date, end_date)
        VALUES %s
        """,
        data
    )
    
    print(f"Inserted {len(data)} new records")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Import account-territory mapping data')
    parser.add_argument('file_path', help='Path to the mapping file (CSV or Excel)')
    parser.add_argument('--account-col', help='Column name for account numbers')
    parser.add_argument('--rep-col', help='Column name for sales representative')
    parser.add_argument('--territory-col', help='Column name for territory')
    parser.add_argument('--region-col', help='Column name for region')
    parser.add_argument('--file-type', choices=['csv', 'excel'], help='File type (auto-detected if not specified)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without actually importing')
    
    args = parser.parse_args()
    
    print("Account Territory Mapping Import Tool")
    print("=" * 40)
    
    # Load configuration
    config = load_config()
    print(f"Using database: {config['db_name']} on {config['db_host']}:{config['db_port']}")
    
    # Read and validate data
    df = read_mapping_file(args.file_path, args.file_type)
    df = validate_data(df)
    
    # If columns weren't specified, show interactive selection
    if not args.account_col:
        print("\nPlease specify the column mappings:")
        print("Available columns:", list(df.columns))
        
        args.account_col = input("Account number column: ").strip()
        args.rep_col = input("Sales rep column (optional, press Enter to skip): ").strip() or None
        args.territory_col = input("Territory column (optional, press Enter to skip): ").strip() or None
        args.region_col = input("Region column (optional, press Enter to skip): ").strip() or None
    
    # Map columns
    mapped_df = map_columns(df, args.account_col, args.rep_col, args.territory_col, args.region_col)
    
    # Import to database
    import_to_database(config, mapped_df, args.dry_run)
    
    print("\nImport completed successfully!")

if __name__ == "__main__":
    main() 