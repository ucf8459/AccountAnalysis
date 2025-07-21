#!/usr/bin/env python3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def create_financial_summary_view():
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
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

if __name__ == "__main__":
    create_financial_summary_view() 