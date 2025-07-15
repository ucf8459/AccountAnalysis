#!/usr/bin/env python3
"""
Import sample_billing data from Excel file into healthtech database using batch processing.
"""

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import sys
from psycopg2.extras import execute_batch
import numpy as np

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

def import_excel_data_batch(config):
    """Import data from Excel file into the database using batch processing."""
    try:
        # Read Excel file
        excel_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'Data',
            'AccountsExport-slaneve-071420251004.xlsx'
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
        
        # Normalize column names to lowercase and underscores
        df.columns = [c.lower().replace(' ', '_').replace('-', '_').replace('__', '_') for c in df.columns]
        
        # Convert NaT and NaN to None for all columns
        df = df.where(pd.notnull(df), None)
        
        # Explicitly convert pd.NaT and 'NaT' in datetime columns to None
        datetime_cols = [col for col in df.columns if 'date' in col or 'billed' in col or 'service' in col or 'thru' in col]
        for col in datetime_cols:
            df[col] = df[col].apply(lambda x: None if pd.isna(x) or x is pd.NaT or x is np.nan or str(x) == 'NaT' else x)
        # Final pass: replace any value that is exactly the string 'NaT' with None
        for col in datetime_cols:
            df[col] = df[col].apply(lambda x: None if x == 'NaT' else x)
        
        # Ensure all values are Python native types (not numpy types)
        df = df.astype(object)
        
        # Deduplicate: keep only the row with the latest placement_date for each client_account_number
        df['placement_date'] = pd.to_datetime(df['placement_date'], errors='coerce')
        df = df.sort_values('placement_date').drop_duplicates('client_account_number', keep='last')

        # Define required datetime columns (excluding 'billed_date')
        required_datetime_cols = ['placement_date', 'service_date_from', 'service_date_thru']

        # Prepare data for batch insert, allowing missing billed_date (replace with '1900-01-01' if missing)
        data_to_insert = []
        for index, row in df.iterrows():
            skip = False
            for col in required_datetime_cols:
                val = row.get(col)
                if val is None or val == '' or (isinstance(val, str) and val.strip() == 'NaT') or pd.isna(val):
                    skip = True
                    break
            if skip:
                continue
            # Handle billed_date: if missing, set to '1900-01-01'
            billed_date = row.get('billed_date')
            if billed_date is None or billed_date == '' or (isinstance(billed_date, str) and billed_date.strip() == 'NaT') or pd.isna(billed_date):
                billed_date = '1900-01-01'
            data_to_insert.append((
                row.get('account_number'),
                billed_date,
                row.get('billing_provider_name'),
                row.get('billing_provider_npi_number'),
                row.get('client_account_number'),
                row.get('current_balance'),
                row.get('facility'),
                row.get('financial_class'),
                row.get('initial_balance'),
                row.get('insurance_cob_sequence'),
                row.get('insurance_group_number'),
                row.get('insurance_name'),
                row.get('medical_record_number'),
                row.get('payer_name_primary'),
                row.get('payer_name_secondary'),
                row.get('place_of_service'),
                row.get('placement_date'),
                row.get('service_date_from'),
                row.get('service_date_thru'),
                row.get('subscriber_id'),
                row.get('total_adjustments'),
                row.get('total_charges'),
                row.get('total_payments'),
                row.get('total_payments_by_insurance'),
                row.get('total_payments_by_patient')
            ))
        
        # Connect to database
        conn = psycopg2.connect(
            host=config['db_host'],
            port=config['db_port'],
            user=config['db_user'],
            password=config['db_password'],
            database=config['db_name']
        )
        cursor = conn.cursor()
        
        # Batch insert
        print("Inserting data in batches...")
        batch_size = 1000
        total_inserted = 0
        errors = 0
        for i in range(0, len(data_to_insert), batch_size):
            batch = data_to_insert[i:i + batch_size]
            try:
                execute_batch(cursor, """
                    INSERT INTO sample_billing (
                        account_number, billed_date, billing_provider_name, billing_provider_npi_number, client_account_number, current_balance, facility, financial_class, initial_balance, insurance_cob_sequence, insurance_group_number, insurance_name, medical_record_number, payer_name_primary, payer_name_secondary, place_of_service, placement_date, service_date_from, service_date_thru, subscriber_id, total_adjustments, total_charges, total_payments, total_payments_by_insurance, total_payments_by_patient
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, batch, page_size=100)
                conn.commit()
                total_inserted += len(batch)
                print(f"Inserted batch {i//batch_size + 1}: {len(batch)} records (Total: {total_inserted})")
            except Exception as e:
                print(f"Error in batch {i//batch_size + 1}: {e}")
                conn.rollback()
                errors += 1
        
        # Verify import
        cursor.execute("SELECT COUNT(*) FROM sample_billing")
        count = cursor.fetchone()[0]
        print(f"\nImport Summary:")
        print(f"Successfully imported: {count} records")
        print(f"Errors encountered: {errors}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error importing data: {e}")
        sys.exit(1)

def main():
    """Main import function."""
    print("Importing sample_billing data from Excel file...")
    
    # Load configuration
    config = load_config()
    print(f"Using database: {config['db_name']} on {config['db_host']}:{config['db_port']}")
    
    # Import data
    import_excel_data_batch(config)
    
    print("\nsample_billing data import completed successfully!")

if __name__ == "__main__":
    main() 