#!/usr/bin/env python3
"""
Import PL Consolidated data into the database.
Creates a table structure suitable for the Company Overview dashboard.
"""

import pandas as pd
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Get database connection."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def create_pl_consolidated_table():
    """Create the PL consolidated table if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS analytics.pl_consolidated (
        id SERIAL PRIMARY KEY,
        metric_type VARCHAR(50) NOT NULL,
        month_name VARCHAR(20) NOT NULL,
        year INTEGER NOT NULL,
        month_number INTEGER NOT NULL,
        amount DECIMAL(15,2) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(metric_type, month_name, year)
    );
    """
    
    try:
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ PL Consolidated table created successfully")
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def import_pl_consolidated_data():
    """Import PL Consolidated data from Excel file."""
    try:
        # Read the Excel file
        df = pd.read_excel('Data/PL Consolidated.xlsx')
        
        # Clean up the data
        df = df.rename(columns={'Unnamed: 0': 'metric_type'})
        
        # Melt the dataframe to convert months to rows
        melted_df = df.melt(
            id_vars=['metric_type'], 
            value_vars=['January', 'February', 'March', 'April', 'May', 'June'],
            var_name='month_name', 
            value_name='amount'
        )
        
        # Add year and month number
        melted_df['year'] = 2025
        month_map = {
            'January': 1, 'February': 2, 'March': 3, 
            'April': 4, 'May': 5, 'June': 6
        }
        melted_df['month_number'] = melted_df['month_name'].map(month_map)
        
        # Clean up metric names
        melted_df['metric_type'] = melted_df['metric_type'].str.strip()
        
        print("📊 Data prepared for import:")
        print(melted_df.head(10))
        print(f"\nTotal rows to import: {len(melted_df)}")
        
        # Connect to database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clear existing data for 2025
        cursor.execute("DELETE FROM analytics.pl_consolidated WHERE year = 2025")
        print("🗑️  Cleared existing 2025 data")
        
        # Insert new data
        insert_sql = """
        INSERT INTO analytics.pl_consolidated 
        (metric_type, month_name, year, month_number, amount) 
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (metric_type, month_name, year) 
        DO UPDATE SET amount = EXCLUDED.amount
        """
        
        for _, row in melted_df.iterrows():
            cursor.execute(insert_sql, (
                row['metric_type'],
                row['month_name'],
                row['year'],
                row['month_number'],
                float(row['amount'])
            ))
        
        conn.commit()
        print("✅ PL Consolidated data imported successfully")
        
        # Verify the import
        cursor.execute("SELECT COUNT(*) FROM analytics.pl_consolidated WHERE year = 2025")
        count = cursor.fetchone()[0]
        print(f"📈 Total records in database: {count}")
        
        # Show sample data
        cursor.execute("""
            SELECT metric_type, month_name, amount 
            FROM analytics.pl_consolidated 
            WHERE year = 2025 
            ORDER BY month_number, metric_type
            LIMIT 10
        """)
        sample_data = cursor.fetchall()
        print("\n📋 Sample imported data:")
        for row in sample_data:
            print(f"  {row[0]}: {row[1]} = ${row[2]:,.2f}")
        
    except Exception as e:
        print(f"❌ Error importing data: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def create_financial_summary_view():
    """Create a view that aggregates PL data for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    create_view_sql = """
    CREATE OR REPLACE VIEW analytics.financial_summary AS
    SELECT 
        year,
        month_number,
        month_name,
        DATE(year || '-' || LPAD(month_number::text, 2, '0') || '-01') as period_start,
        DATE(year || '-' || LPAD(month_number::text, 2, '0') || '-' || 
             EXTRACT(DAY FROM DATE(year || '-' || LPAD(month_number::text, 2, '0') || '-01') + INTERVAL '1 month - 1 day')) as period_end,
        MAX(CASE WHEN metric_type = 'Revenue' THEN amount ELSE 0 END) as total_revenue,
        MAX(CASE WHEN metric_type = 'COGS' THEN amount ELSE 0 END) as total_cogs,
        MAX(CASE WHEN metric_type = 'Expense' THEN amount ELSE 0 END) as total_expenses,
        MAX(CASE WHEN metric_type = 'Revenue' THEN amount ELSE 0 END) - 
        MAX(CASE WHEN metric_type = 'COGS' THEN amount ELSE 0 END) as gross_profit,
        MAX(CASE WHEN metric_type = 'Net Income' THEN amount ELSE 0 END) as net_profit
    FROM analytics.pl_consolidated
    GROUP BY year, month_number, month_name
    ORDER BY year, month_number;
    """
    
    try:
        cursor.execute(create_view_sql)
        conn.commit()
        print("✅ Financial summary view created successfully")
        
        # Test the view
        cursor.execute("SELECT * FROM analytics.financial_summary ORDER BY period_start LIMIT 5")
        test_data = cursor.fetchall()
        print("\n📊 Financial summary view test data:")
        for row in test_data:
            print(f"  {row[2]} {row[0]}: Revenue=${row[5]:,.0f}, COGS=${row[6]:,.0f}, Net=${row[9]:,.0f}")
            
    except Exception as e:
        print(f"❌ Error creating view: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to run the import process."""
    print("🚀 Starting PL Consolidated data import...")
    
    # Create table
    create_pl_consolidated_table()
    
    # Import data
    import_pl_consolidated_data()
    
    # Create financial summary view
    create_financial_summary_view()
    
    print("\n🎉 PL Consolidated import completed successfully!")
    print("\nThe Company Overview dashboard should now display real data from the PL Consolidated file.")

if __name__ == "__main__":
    main() 