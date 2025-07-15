#!/usr/bin/env python3
"""
Import COGS Expense data from Excel spreadsheet into database.
"""

import pandas as pd
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection."""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not found in .env file")
    return psycopg2.connect(database_url)

def import_cogs_expense_data():
    """Import COGS Expense data from Excel file."""
    try:
        # Read the Excel file
        df = pd.read_excel('Data/COGS Expense.xlsx')
        
        # Clean up the data
        # The first column contains month/year and type info
        df = df.rename(columns={'Unnamed: 0': 'description'})
        
        # Parse the description column to extract month/year and type
        parsed_data = []
        for _, row in df.iterrows():
            description = row['description']
            
            # Parse description like "March 2025 COGS" or "March 2025 Expense"
            parts = description.split()
            if len(parts) >= 3:
                month = parts[0]
                year = parts[1]
                expense_type = parts[2]
                month_year = f"{month} {year}"
                
                # Process each territory
                territories = ['Alpha', 'Bravo', 'Charlie', 'Delta', 'Echo', 'Foxtrot']
                for territory in territories:
                    if territory in row and pd.notna(row[territory]):
                        amount = float(row[territory])
                        parsed_data.append({
                            'territory': territory,
                            'month_year': month_year,
                            'expense_type': expense_type,
                            'amount': amount
                        })
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        cursor.execute("DELETE FROM cogs_expense")
        print(f"Cleared existing COGS Expense data")
        
        # Insert the data
        for data in parsed_data:
            cursor.execute("""
                INSERT INTO cogs_expense (territory, month_year, expense_type, amount)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (territory, month_year, expense_type) 
                DO UPDATE SET 
                    amount = EXCLUDED.amount,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                data['territory'],
                data['month_year'],
                data['expense_type'],
                data['amount']
            ))
        
        conn.commit()
        print(f"Successfully imported {len(parsed_data)} COGS Expense records")
        
        # Verify the import
        cursor.execute("SELECT COUNT(*) FROM cogs_expense")
        count = cursor.fetchone()[0]
        print(f"Total records in cogs_expense table: {count}")
        
        # Show sample data
        cursor.execute("SELECT * FROM cogs_expense ORDER BY month_year, territory, expense_type LIMIT 10")
        sample_data = cursor.fetchall()
        print("\nSample imported data:")
        for row in sample_data:
            print(f"  {row[1]} | {row[2]} | {row[3]} | ${row[4]:,.2f}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error importing COGS Expense data: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import_cogs_expense_data() 