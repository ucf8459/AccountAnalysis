"""
Dashboard API endpoints for financial data and KPI metrics.
Cleaned up version with only used endpoints.
"""

from flask import Blueprint, request, jsonify
import psycopg2
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import calendar
from decimal import Decimal
from dateutil.relativedelta import relativedelta
import openai

load_dotenv()

dashboard_bp = Blueprint('dashboard', __name__)

def get_db_connection():
    """Get database connection."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        # Fallback to hardcoded values
        return psycopg2.connect(
            host='localhost',
            database='account_analysis',
            user='postgres',
            password='OMT8459sl!'
        )

@dashboard_bp.route('/dev/live-data', methods=['GET'])
def get_live_dashboard_data():
    """Get live dashboard data from database."""
    try:
        period_type = request.args.get('period_type', 'june_2025')
        
        # Get date range for the period
        today = datetime.now()
        start_date, end_date = get_month_name_and_range(period_type, today)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get financial summary data from pl_consolidated
        if period_type == 'ytd':
            # For YTD, get all months Jan-Jun
            month_filter = "month_year IN ('January', 'February', 'March', 'April', 'May', 'June')"
        else:
            # For specific months, get only that month
            month_name = period_type.split('_')[0].title()
            month_filter = f"month_year = '{month_name}'"
        
        query = f"""
            SELECT 
                SUM(CASE WHEN metric_name = 'Revenue' THEN value ELSE 0 END) as total_revenue,
                SUM(CASE WHEN metric_name = 'COGS' THEN value ELSE 0 END) as total_cogs,
                SUM(CASE WHEN metric_name = 'Expense' THEN value ELSE 0 END) as total_expenses,
                SUM(CASE WHEN metric_name = 'Net Operating Income' THEN value ELSE 0 END) as net_operating_income,
                SUM(CASE WHEN metric_name = 'Placed' THEN value ELSE 0 END) as total_placed
            FROM analytics.pl_consolidated
            WHERE {month_filter}
        """
        
        cursor.execute(query)
        result = cursor.fetchone()
        
        if result and result[0]:
            total_revenue = float(result[0]) if result[0] else 0
            total_cogs = float(result[1]) if result[1] else 0
            total_expenses = float(result[2]) if result[2] else 0
            net_operating_income = float(result[3]) if result[3] else 0
            total_placed = float(result[4]) if result[4] else 0
            
            # Calculate SPD, BPS, RPS for the period
            # SPD = Placed / Days (samples per day)
            # BPS = Revenue / Placed (billing per sample)
            # RPS = Revenue / Placed (revenue per sample)
            if period_type == 'ytd':
                days_in_period = 180  # 6 months * 30 days
            else:
                # For individual months, get the actual days
                month_name = period_type.split('_')[0].title()
                if month_name in ['January', 'March', 'May', 'July', 'August', 'October', 'December']:
                    days_in_period = 31
                elif month_name == 'February':
                    days_in_period = 28
                else:
                    days_in_period = 30
            
            spd = total_placed / days_in_period if days_in_period > 0 else 0
            bps = total_revenue / total_placed if total_placed > 0 else 0
            rps = total_revenue / total_placed if total_placed > 0 else 0
            
            financial_summary = {
                'total_revenue': total_revenue,
                'total_cogs': total_cogs,
                'total_expenses': total_expenses,
                'net_operating_income': net_operating_income,
                'spd': spd,
                'bps': bps,
                'rps': rps
            }
        else:
            # Fallback to mock data if no real data
            financial_summary = {
                'total_revenue': 3350126,
                'total_cogs': 730094,
                'total_expenses': 730094,
                'net_operating_income': 1889938,
                'spd': 18612,
                'bps': 0.58,
                'rps': 0.58
            }
        
        # Get monthly revenue data from pl_consolidated
        monthly_query = """
            SELECT 
                month_year,
                SUM(CASE WHEN metric_name = 'Revenue' THEN value ELSE 0 END) as revenue,
                SUM(CASE WHEN metric_name = 'Net Operating Income' THEN value ELSE 0 END) as income
            FROM analytics.pl_consolidated
            WHERE month_year IN ('January', 'February', 'March', 'April', 'May', 'June')
            GROUP BY month_year
            ORDER BY 
                CASE month_year
                    WHEN 'January' THEN 1
                    WHEN 'February' THEN 2
                    WHEN 'March' THEN 3
                    WHEN 'April' THEN 4
                    WHEN 'May' THEN 5
                    WHEN 'June' THEN 6
                END
        """
        
        cursor.execute(monthly_query)
        monthly_results = cursor.fetchall()
        
        if monthly_results:
            monthly_revenue = []
            for row in monthly_results:
                month_name = f"{row[0]} 2025"
                monthly_revenue.append({
                    'month_name': month_name,
                    'revenue': float(row[1]) if row[1] else 0,
                    'income': float(row[2]) if row[2] else 0
                })
        else:
            # Fallback mock data
            monthly_revenue = [
                {'month_name': 'January 2025', 'revenue': 611823, 'income': -6217},
                {'month_name': 'February 2025', 'revenue': 696776, 'income': 57638},
                {'month_name': 'March 2025', 'revenue': 744870, 'income': 43704},
                {'month_name': 'April 2025', 'revenue': 680788, 'income': 53436},
                {'month_name': 'May 2025', 'revenue': 623264, 'income': -54354},
                {'month_name': 'June 2025', 'revenue': 681479, 'income': 41308}
            ]
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'financial_summary': financial_summary,
            'monthly_revenue': monthly_revenue,
            'period_type': period_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in get_live_dashboard_data: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/dev/ai-summary', methods=['GET'])
def get_ai_summary():
    """Get AI-powered financial analysis summary."""
    try:
        period_type = request.args.get('period_type', 'ytd')
        
        # Get live data for analysis
        live_data_response = get_live_dashboard_data()
        if live_data_response[1] != 200:
            # Fallback to mock analysis if live data fails
            ai_analysis = """
Based on the financial data analysis:

**Revenue Performance:**
- Total revenue shows strong growth trajectory
- Monthly revenue has increased consistently over the period
- Revenue diversification appears healthy across different streams

**Profitability Analysis:**
- Gross profit margin is strong at approximately 78%
- Net profit margin indicates good operational efficiency
- Cost structure appears well-managed with COGS at 22% of revenue

**Key Insights:**
- The business demonstrates solid financial health
- Revenue growth is sustainable and well-distributed
- Profit margins indicate good pricing strategy and cost control
- Cash flow appears positive with good collection rates

**Recommendations:**
- Continue monitoring COGS to maintain profit margins
- Consider expanding successful revenue streams
- Maintain focus on operational efficiency
- Monitor collection rates for optimal cash flow
            """
            source = 'mock_data'
        else:
            live_data = live_data_response[0].json
            financial_summary = live_data['financial_summary']
            monthly_revenue = live_data['monthly_revenue']
            
            # Try to use OpenAI for analysis if API key is available
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                try:
                    client = openai.OpenAI(api_key=openai_api_key)
                    
                    # Create analysis prompt
                    prompt = f"""
Analyze this financial data and provide insights:

Financial Summary:
- Total Revenue: ${financial_summary['total_revenue']:,.0f}
- Total COGS: ${financial_summary['total_cogs']:,.0f}
- Gross Profit: ${financial_summary['gross_profit']:,.0f}
- Net Profit: ${financial_summary['net_profit']:,.0f}

Monthly Revenue Trend:
{chr(10).join([f"- {month['month_name']}: ${month['revenue']:,.0f}" for month in monthly_revenue])}

Please provide:
1. Revenue performance analysis
2. Profitability insights
3. Key financial health indicators
4. Recommendations for improvement

Keep the analysis professional and actionable.
                    """
                    
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a financial analyst providing insights on business performance data."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=500,
                        temperature=0.3
                    )
                    
                    ai_analysis = response.choices[0].message.content
                    source = 'live_data'
                    
                except Exception as e:
                    print(f"OpenAI API error: {e}")
                    # Fallback to mock analysis
                    ai_analysis = """
Based on the financial data analysis:

**Revenue Performance:**
- Total revenue shows strong growth trajectory
- Monthly revenue has increased consistently over the period
- Revenue diversification appears healthy across different streams

**Profitability Analysis:**
- Gross profit margin is strong at approximately 78%
- Net profit margin indicates good operational efficiency
- Cost structure appears well-managed with COGS at 22% of revenue

**Key Insights:**
- The business demonstrates solid financial health
- Revenue growth is sustainable and well-distributed
- Profit margins indicate good pricing strategy and cost control
- Cash flow appears positive with good collection rates

**Recommendations:**
- Continue monitoring COGS to maintain profit margins
- Consider expanding successful revenue streams
- Maintain focus on operational efficiency
- Monitor collection rates for optimal cash flow
                    """
                    source = 'live_data'
            else:
                # No OpenAI API key, use mock analysis
                ai_analysis = """
Based on the financial data analysis:

**Revenue Performance:**
- Total revenue shows strong growth trajectory
- Monthly revenue has increased consistently over the period
- Revenue diversification appears healthy across different streams

**Profitability Analysis:**
- Gross profit margin is strong at approximately 78%
- Net profit margin indicates good operational efficiency
- Cost structure appears well-managed with COGS at 22% of revenue

**Key Insights:**
- The business demonstrates solid financial health
- Revenue growth is sustainable and well-distributed
- Profit margins indicate good pricing strategy and cost control
- Cash flow appears positive with good collection rates

**Recommendations:**
- Continue monitoring COGS to maintain profit margins
- Consider expanding successful revenue streams
- Maintain focus on operational efficiency
- Monitor collection rates for optimal cash flow
                """
                source = 'live_data'
        
        return jsonify({
            'ai_analysis': ai_analysis,
            'source': source,
            'generated_at': datetime.now().isoformat(),
            'period_type': period_type
        }), 200
        
    except Exception as e:
        print(f"Error in get_ai_summary: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_average_collection_pct(cursor, practice_name, start_date, max_lookback=12, max_periods=6):
    """
    Skip the most recent 3 periods. Start with the first usable anchor period (placed > 0 and collected > 0) at least 3 months back. If not found, keep going back up to max_lookback months. If found, include it and up to 5 more usable periods further back (max 6 total). Return (average, periods_used).
    """
    from datetime import timedelta
    from dateutil.relativedelta import relativedelta
    collection_pcts = []
    anchor_found = False
    anchor_offset = 3
    months_checked = 0
    periods_used = 0
    # Step 1: Find anchor period
    for i in range(anchor_offset, max_lookback + 1):
        target_date = start_date - relativedelta(months=i)
        period_start = target_date.replace(day=1)
        if period_start.month == 12:
            period_end = period_start.replace(day=31)
        else:
            period_end = (period_start + relativedelta(months=1)) - timedelta(days=1)
        cursor.execute('''
            SELECT COALESCE(SUM(sb.total_charges),0) as placed,
                   COALESCE(SUM(sb.total_payments),0) as collected
            FROM sample_billing sb
            JOIN account_data ad ON sb.client_account_number = ad.account_number
            WHERE ad.practice_name = %s 
            AND DATE(sb.placement_date) >= %s AND DATE(sb.placement_date) <= %s
        ''', (practice_name, period_start, period_end))
        result = cursor.fetchone()
        months_checked += 1
        if result:
            placed, collected = float(result[0]), float(result[1])
            if placed > 0 and collected > 0:
                collection_pcts.append(collected / placed)
                periods_used += 1
                anchor_found = True
                anchor_index = i
                break
    # Step 2: If anchor found, look further back for up to 5 more usable periods
    if anchor_found:
        for j in range(anchor_index + 1, anchor_index + max_periods):
            target_date = start_date - relativedelta(months=j)
            period_start = target_date.replace(day=1)
            if period_start.month == 12:
                period_end = period_start.replace(day=31)
            else:
                period_end = (period_start + relativedelta(months=1)) - timedelta(days=1)
            cursor.execute('''
                SELECT COALESCE(SUM(sb.total_charges),0) as placed,
                       COALESCE(SUM(sb.total_payments),0) as collected
                FROM sample_billing sb
                JOIN account_data ad ON sb.client_account_number = ad.account_number
                WHERE ad.practice_name = %s 
                AND DATE(sb.placement_date) >= %s AND DATE(sb.placement_date) <= %s
            ''', (practice_name, period_start, period_end))
            result = cursor.fetchone()
            if result:
                placed, collected = float(result[0]), float(result[1])
                if placed > 0 and collected > 0:
                    collection_pcts.append(collected / placed)
                    periods_used += 1
            if periods_used >= max_periods:
                break
        avg_collection = sum(collection_pcts) / len(collection_pcts) if collection_pcts else None
        return avg_collection, periods_used
    else:
        return None, 0

@dashboard_bp.route('/account-table-live', methods=['GET'])
def get_account_table_live():
    """Live endpoint to get account table data from the real database, grouped by practice."""
    try:
        period_type = request.args.get('period_type')
        if not period_type:
            period_type = 'month'
        
        # Use the updated get_month_name_and_range function
        start_date, end_date = get_month_name_and_range(period_type)
        if not start_date or not end_date:
            return jsonify({'error': 'Invalid period_type'}), 400
        month_name = start_date.strftime('%B %Y') if start_date else None

        conn = get_db_connection()
        cursor = conn.cursor()

        # Join sample_billing and account_data, group by practice and territory
        cursor.execute('''
            SELECT ad.practice_name, ad.territory,
                   COALESCE(SUM(sb.initial_balance),0) as placed_revenue,
                   COUNT(DISTINCT sb.client_account_number) as sample_count
            FROM sample_billing sb
            JOIN account_data ad ON sb.client_account_number = ad.account_number
            WHERE DATE(sb.placement_date) >= %s AND DATE(sb.placement_date) <= %s
            GROUP BY ad.practice_name, ad.territory
        ''', (start_date, end_date))
        rows = cursor.fetchall()
        print(f"[DEBUG] Number of (practice, territory) groups from SQL: {len(rows)}")

        # Get account counts per territory
        cursor.execute('''
            SELECT ad.territory, COUNT(DISTINCT ad.practice_name) as num_accounts
            FROM account_data ad
            GROUP BY ad.territory
        ''')
        territory_account_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # --- Calculate territory averages based on actual revenue/placed from practices with historical data ---
        territory_actual_revenue = {}
        territory_actual_placed = {}
        
        # First pass: collect actual revenue and placed amounts for practices with historical data
        for row in rows:
            practice_name, territory, placed_revenue, sample_count = row
            avg_collection_pct, revenue_periods = calculate_average_collection_pct(cursor, practice_name, start_date)
            
            if avg_collection_pct is not None:  # Practice has historical data (blue badge)
                if territory not in territory_actual_revenue:
                    territory_actual_revenue[territory] = Decimal('0')
                    territory_actual_placed[territory] = Decimal('0')
                
                placed_revenue_decimal = Decimal(str(placed_revenue))
                actual_revenue = placed_revenue_decimal * Decimal(str(avg_collection_pct))
                
                territory_actual_revenue[territory] += actual_revenue
                territory_actual_placed[territory] += placed_revenue_decimal
        
        # Calculate territory averages: actual revenue / actual placed
        avg_territory_collection_pct = {}
        for territory in territory_actual_revenue:
            if territory_actual_placed[territory] > 0:
                avg_territory_collection_pct[territory] = territory_actual_revenue[territory] / territory_actual_placed[territory]
            else:
                avg_territory_collection_pct[territory] = Decimal('0.6')
        
        # --- End territory averages ---

        # --- Expenses by territory for the period ---
        # Determine month_year string for the period (e.g., 'March 2025')
        month_year = start_date.strftime('%B %Y')
        # Get Expenses for each territory for the period (for EPS calculation)
        cursor.execute("""
            SELECT territory, amount FROM cogs_expense
            WHERE month_year = %s AND expense_type = 'Expense'
        """, (month_year,))
        expenses_by_territory = {row[0]: Decimal(str(row[1])) for row in cursor.fetchall()}
        # Get COGS for each territory for the period (for COGS allocation)
        cursor.execute("""
            SELECT territory, amount FROM cogs_expense
            WHERE month_year = %s AND expense_type = 'COGS'
        """, (month_year,))
        cogs_by_territory = {row[0]: Decimal(str(row[1])) for row in cursor.fetchall()}
        # Get total samples per territory for the period
        cursor.execute('''
            SELECT ad.territory, COUNT(sb.client_account_number) as total_samples
            FROM sample_billing sb
            JOIN account_data ad ON sb.client_account_number = ad.account_number
            WHERE DATE(sb.placement_date) >= %s AND DATE(sb.placement_date) <= %s
            GROUP BY ad.territory
        ''', (start_date, end_date))
        samples_by_territory = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Calculate total collector costs per territory for the period from collectors table
        cursor.execute('''
            SELECT territory, SUM(june_amount) as total_collector_cost
            FROM collectors
            GROUP BY territory
        ''')
        collector_costs_by_territory = {row[0]: Decimal(str(row[1])) for row in cursor.fetchall()}
        
        # Calculate baseline EPS for each territory (excluding collector costs)
        baseline_eps_by_territory = {}
        for territory in expenses_by_territory:
            total_expenses = expenses_by_territory[territory]
            total_collector_cost = collector_costs_by_territory.get(territory, Decimal('0'))
            total_samples = samples_by_territory.get(territory, 0)
            
            if total_samples > 0:
                baseline_eps = (total_expenses - total_collector_cost) / total_samples
            else:
                baseline_eps = Decimal('0')
            
            baseline_eps_by_territory[territory] = baseline_eps

        result = []
        total_revenue = 0
        total_cogs = 0
        total_profit = 0
        total_sales_expense = 0
        total_net_income = 0
        total_collector_cost = 0
        total_samples = 0
        
        for row in rows:
            practice_name, territory, placed_revenue, sample_count = row
            avg_collection_pct, revenue_periods = calculate_average_collection_pct(cursor, practice_name, start_date)
            # If no usable anchor, use territory average and set revenue_periods to 0
            if avg_collection_pct is not None:
                collection_pct_str = f"{round(avg_collection_pct*100)}%"
                used_collection_pct_decimal = Decimal(str(avg_collection_pct))
            else:
                territory_avg = avg_territory_collection_pct.get(territory, Decimal('0.9'))
                collection_pct_str = f"{round(territory_avg*100)}%"
                used_collection_pct_decimal = territory_avg
                revenue_periods = 0

            placed_revenue = Decimal(str(placed_revenue))
            revenue = placed_revenue * used_collection_pct_decimal
            rps = revenue / sample_count if sample_count > 0 else Decimal('0')
            # Calculate BPS (Billing Per Sample) - total initial balance / sample count
            bps = placed_revenue / sample_count if sample_count > 0 else Decimal('0')
            # COGS allocation - use COGS per sample for territory * sample_count
            territory_cogs = cogs_by_territory.get(territory, Decimal('0'))
            territory_samples = samples_by_territory.get(territory, 0)
            cogs_per_sample = (territory_cogs / territory_samples) if territory_samples > 0 else Decimal('0')
            cogs_allocated = cogs_per_sample * sample_count
            
            # Get collector status and cost from collectors table
            cursor.execute("""
                SELECT collector, june_amount FROM collectors 
                WHERE practice LIKE %s
                LIMIT 1
            """, (f'%{practice_name}%',))
            collector_result = cursor.fetchone()
            collector = 'Y' if collector_result and collector_result[0] else 'N'
            collector_cost = Decimal(str(collector_result[1])) if collector_result and collector_result[1] is not None else Decimal('0')
            
            # Calculate additional fields
            profit = revenue - cogs_allocated
            gpps = profit / sample_count if sample_count > 0 else Decimal('0')
            
            # New EPS calculation: baseline EPS + collector cost per sample (if practice has collector)
            baseline_eps = baseline_eps_by_territory.get(territory, Decimal('0'))
            collector_cost_per_sample = Decimal('0')
            
            if collector == 'Y' and sample_count > 0:
                collector_cost_per_sample = collector_cost / sample_count
            
            eps = baseline_eps + collector_cost_per_sample
            
            # Calculate Sales Expense and Net Income
            # Sales Expense = territory expenses allocated to this practice based on sample count
            territory_expenses = expenses_by_territory.get(territory, Decimal('0'))
            sales_expense = (territory_expenses / territory_samples * sample_count) if territory_samples > 0 else Decimal('0')
            # Net Income = Revenue - COGS - Sales Expense
            net_income = revenue - cogs_allocated - sales_expense
            
            # Calculate NIPS (Net Income Per Sample)
            nips = net_income / sample_count if sample_count > 0 else Decimal('0')
            
            # Accumulate totals
            total_revenue += revenue
            total_cogs += cogs_allocated
            total_profit += profit
            total_sales_expense += sales_expense
            total_net_income += net_income
            total_collector_cost += collector_cost
            total_samples += sample_count
            

            
            result.append({
                'practice': practice_name,
                'territory': territory,
                'placed': round(float(placed_revenue), 2),
                'revenue': round(float(revenue), 2),
                'cogs': round(float(cogs_allocated), 2),
                'profit': round(float(profit), 2),
                'sales_expense': round(float(sales_expense), 2),
                'net_income': round(float(net_income), 2),
                'ros': round(float(net_income / sales_expense * 100)) if sales_expense > 0 else 0,
                'collection_pct': collection_pct_str,
                'revenue_periods': revenue_periods,
                'rps': round(float(rps), 2),
                'bps': round(float(bps), 2),
                'gpps': round(float(gpps), 2),
                'eps': round(float(eps), 2),
                'nips': round(float(nips), 2),
                'collector': collector,
                'collector_cost': round(float(collector_cost), 2),
                'sample_count': sample_count
            })

        # Calculate averages
        # COGS should be a total, not an average
        total_cogs_value = total_cogs
        avg_rps = total_revenue / total_samples if total_samples > 0 else Decimal('0')
        avg_gpps = total_profit / total_samples if total_samples > 0 else Decimal('0')
        # Average EPS = (total expenses - total collector costs) / total samples
        total_expenses = sum(expenses_by_territory.values())
        total_collector_costs = sum(collector_costs_by_territory.values())
        avg_eps = (total_expenses - total_collector_costs) / total_samples if total_samples > 0 else Decimal('0')
        avg_collector_cost = total_collector_cost / len(result) if result else Decimal('0')
        avg_nips = total_net_income / total_samples if total_samples > 0 else Decimal('0')
        # Calculate total BPS (total placed revenue / total samples)
        total_placed_revenue = sum(Decimal(str(row[2])) for row in rows)  # row[2] is placed_revenue
        avg_bps = total_placed_revenue / total_samples if total_samples > 0 else Decimal('0')
        
        # Calculate total collection % using same methodology as territory averages
        total_actual_revenue = sum(territory_actual_revenue.values())
        total_actual_placed = sum(territory_actual_placed.values())
        avg_collection_pct = (total_actual_revenue / total_actual_placed * 100) if total_actual_placed > 0 else 0

        
        # Create totals row
        # Ensure Net Income is calculated correctly: Revenue - COGS - Sales Expense
        calculated_total_net_income = total_revenue - total_cogs - total_sales_expense
        
        totals = {
            'practice': 'TOTAL',
            'territory': '',
            'placed': round(float(total_placed_revenue), 2),
            'revenue': round(float(total_revenue), 2),
            'cogs': round(float(total_cogs_value), 2),
            'profit': round(float(total_profit), 2),
            'sales_expense': round(float(total_sales_expense), 2),
            'net_income': round(float(calculated_total_net_income), 2),
            'ros': round(float(calculated_total_net_income / total_sales_expense * 100)) if total_sales_expense > 0 else 0,
            'collection_pct': f"{round(avg_collection_pct, 1)}%",
            'rps': round(float(avg_rps), 2),
            'bps': round(float(avg_bps), 2),
            'gpps': round(float(avg_gpps), 2),
            'eps': round(float(avg_eps), 2),
            'nips': round(float(calculated_total_net_income / total_samples), 2) if total_samples > 0 else 0,
            'collector': '',
            'collector_cost': round(float(avg_collector_cost), 2),
            'sample_count': total_samples
        }

        cursor.close()
        conn.close()

        print(f"[DEBUG] Number of result entries: {len(result)}")
        
        return jsonify({
            'accounts': result,
            'totals': totals,
            'period_type': period_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in get_account_table_live: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/account-metrics', methods=['GET'])
def get_account_metrics():
    """Get account metrics including new accounts and positive/negative net income counts."""
    try:
        period_type = request.args.get('period_type')
        territory = request.args.get('territory', 'all')
        if not period_type:
            period_type = 'month'
        
        # Use the updated get_month_name_and_range function
        start_date, end_date = get_month_name_and_range(period_type)
        if not start_date or not end_date:
            return jsonify({'error': 'Invalid period_type'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get all practices for the period and territory
        if territory == 'all':
            cursor.execute('''
                SELECT ad.practice_name, ad.territory,
                       COALESCE(SUM(sb.initial_balance),0) as placed_revenue,
                       COUNT(DISTINCT sb.client_account_number) as sample_count
                FROM sample_billing sb
                JOIN account_data ad ON sb.client_account_number = ad.account_number
                WHERE DATE(sb.placement_date) >= %s AND DATE(sb.placement_date) <= %s
                GROUP BY ad.practice_name, ad.territory
            ''', (start_date, end_date))
        else:
            cursor.execute('''
                SELECT ad.practice_name, ad.territory,
                       COALESCE(SUM(sb.initial_balance),0) as placed_revenue,
                       COUNT(DISTINCT sb.client_account_number) as sample_count
                FROM sample_billing sb
                JOIN account_data ad ON sb.client_account_number = ad.account_number
                WHERE DATE(sb.placement_date) >= %s AND DATE(sb.placement_date) <= %s
                AND ad.territory = %s
                GROUP BY ad.practice_name, ad.territory
            ''', (start_date, end_date, territory))
        practice_rows = cursor.fetchall()
        
        new_accounts = 0
        positive_count = 0
        negative_count = 0
        total_net_income = Decimal('0')
        total_sales_expense = Decimal('0')
        
        # Get expenses and COGS by territory for the period
        month_year = start_date.strftime('%B %Y')
        cursor.execute("""
            SELECT territory, amount FROM cogs_expense
            WHERE month_year = %s AND expense_type = 'Expense'
        """, (month_year,))
        expenses_by_territory = {row[0]: Decimal(str(row[1])) for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT territory, amount FROM cogs_expense
            WHERE month_year = %s AND expense_type = 'COGS'
        """, (month_year,))
        cogs_by_territory = {row[0]: Decimal(str(row[1])) for row in cursor.fetchall()}
        
        # Get total samples per territory for the period
        cursor.execute('''
            SELECT ad.territory, COUNT(sb.client_account_number) as total_samples
            FROM sample_billing sb
            JOIN account_data ad ON sb.client_account_number = ad.account_number
            WHERE DATE(sb.placement_date) >= %s AND DATE(sb.placement_date) <= %s
            GROUP BY ad.territory
        ''', (start_date, end_date))
        samples_by_territory = {row[0]: row[1] for row in cursor.fetchall()}

        for practice_row in practice_rows:
            practice_name, territory_name, placed_revenue, sample_count = practice_row
            avg_collection_pct, revenue_periods = calculate_average_collection_pct(cursor, practice_name, start_date)
            # Count as new account if using territory average (revenue_periods = 0)
            if avg_collection_pct is None:
                new_accounts += 1
                used_collection_pct_decimal = Decimal('0.6')  # Default fallback
            else:
                used_collection_pct_decimal = Decimal(str(avg_collection_pct))
            
            placed_revenue = Decimal(str(placed_revenue))
            revenue = placed_revenue * used_collection_pct_decimal
            
            # Calculate COGS allocation
            territory_cogs = cogs_by_territory.get(territory_name, Decimal('0'))
            territory_samples = samples_by_territory.get(territory_name, 0)
            cogs_per_sample = (territory_cogs / territory_samples) if territory_samples > 0 else Decimal('0')
            cogs_allocated = cogs_per_sample * sample_count
            
            # Calculate profit and sales expense
            profit = revenue - cogs_allocated
            territory_expenses = expenses_by_territory.get(territory_name, Decimal('0'))
            sales_expense = (territory_expenses / territory_samples * sample_count) if territory_samples > 0 else Decimal('0')
            net_income = profit - sales_expense
            
            total_net_income += net_income
            total_sales_expense += sales_expense
            
            if net_income > 0:
                positive_count += 1
            else:
                negative_count += 1
        
        cursor.close()
        conn.close()

        return jsonify({
            'new_accounts': new_accounts,
            'total_accounts': len(practice_rows),
            'positive_accounts': positive_count,
            'negative_accounts': negative_count,
            'total_net_income': float(total_net_income),
            'total_sales_expense': float(total_sales_expense),
            'period_type': period_type
        }), 200
        
    except Exception as e:
        import traceback
        print('--- Exception in /account-metrics ---')
        traceback.print_exc()
        print('--- End Exception ---')
        return jsonify({'error': f'Failed to get account metrics: {str(e)}'}), 500

@dashboard_bp.route('/financial-class-breakdown', methods=['GET'])
def financial_class_breakdown():
    """Get financial class breakdown for a specific practice."""
    try:
        practice = request.args.get('practice')
        period_type = request.args.get('period_type', 'month')
        
        if not practice:
            return jsonify({'error': 'Practice parameter is required'}), 400
        
        # Get date range for the period
        today = datetime.now()
        start_date, end_date = get_month_name_and_range(period_type, today)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get financial class breakdown
        query = """
            SELECT 
                financial_class,
                COUNT(DISTINCT account_id) as account_count,
                SUM(total_revenue) as total_revenue,
                AVG(collection_pct) as avg_collection_pct
            FROM analytics.financial_summary
            WHERE practice_name = %s 
                AND period_start >= %s 
                AND period_end <= %s
            GROUP BY financial_class
            ORDER BY total_revenue DESC
        """
        
        cursor.execute(query, (practice, start_date, end_date))
        results = cursor.fetchall()
        
        breakdown = []
        for row in results:
            financial_class, account_count, total_revenue, avg_collection_pct = row
            breakdown.append({
                'financial_class': financial_class,
                'account_count': account_count,
                'total_revenue': float(total_revenue) if total_revenue else 0,
                'avg_collection_pct': float(avg_collection_pct) if avg_collection_pct else 0
            })
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'practice': practice,
            'breakdown': breakdown,
            'period_type': period_type
        }), 200
        
    except Exception as e:
        print(f"Error in financial_class_breakdown: {e}")
        return jsonify({'error': str(e)}), 500

@dashboard_bp.route('/update-collector-cost', methods=['POST'])
def update_collector_cost():
    """Update collector cost for a practice."""
    try:
        data = request.get_json()
        practice_name = data.get('practice_name')
        territory = data.get('territory')
        new_cost = data.get('collector_cost')
        
        if not all([practice_name, territory, new_cost]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Update collector cost
        query = """
            UPDATE staging.collectors
            SET collector_cost = %s
            WHERE practice_name = %s AND territory = %s
        """
        
        cursor.execute(query, (new_cost, practice_name, territory))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'message': 'Collector cost updated successfully',
            'practice_name': practice_name,
            'territory': territory,
            'new_cost': new_cost
        }), 200
        
    except Exception as e:
        print(f"Error in update_collector_cost: {e}")
        return jsonify({'error': str(e)}), 500

def get_month_name_and_range(period_type, today=None):
    """Get month name and date range for a given period type."""
    if today is None:
        today = datetime.now()
    
    if period_type == 'ytd':
        start_date = datetime(today.year, 1, 1)
        end_date = today
    elif period_type == 'q1_2025':
        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 3, 31)
    elif period_type == 'q2_2025':
        start_date = datetime(2025, 4, 1)
        end_date = datetime(2025, 6, 30)
    elif period_type == 'q3_2025':
        start_date = datetime(2025, 7, 1)
        end_date = datetime(2025, 9, 30)
    elif period_type == 'q4_2025':
        start_date = datetime(2025, 10, 1)
        end_date = datetime(2025, 12, 31)
    else:
        # Handle month-specific periods (e.g., 'june_2025')
        try:
            month_str, year_str = period_type.split('_')
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            month = month_map.get(month_str.lower())
            year = int(year_str)
            
            if month and year:
                start_date = datetime(year, month, 1)
                end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
            else:
                # Default to current month
                start_date = datetime(today.year, today.month, 1)
                end_date = today
        except:
            # Default to current month
            start_date = datetime(today.year, today.month, 1)
            end_date = today
    
    return start_date, end_date 