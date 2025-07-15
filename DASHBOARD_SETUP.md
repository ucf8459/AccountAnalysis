# Dashboard Setup and Usage

## Overview
The Account Analysis Dashboard is a comprehensive financial analytics tool that provides insights into company performance, territory analysis, and account-level KPIs.

## Quick Start

### 1. Start the Application
```bash
# Start the Flask application on port 5001 (to avoid conflicts with AirPlay)
PORT=5001 python app.py
```

### 2. Access the Dashboard
Open your browser and navigate to:
```
http://localhost:5001/dashboard
```

## Features

### Company Overview Section
- **KPI Cards**: Total Income, COGS, Gross Profit, Net Income
- **Revenue Chart**: Monthly revenue trends with income overlay
- **Key Ratios**: TAT, COS%, Digital Orders%, Active Accounts, Revenue Per Sample, Collection%
- **Top Practices**: Table of top 10 practices by revenue

### Territories Section
- **Territory Performance**: Revenue, GP%, COS%, Collection% by territory
- **ROS Analysis**: Return on Sales metrics for each territory
- **Sparkline Charts**: Quarter and YTD trends for each territory
- **Expandable Details**: Click to view detailed territory information

### Accounts Section
- **Account Filtering**: Filter by territory
- **KPI Metrics**: BPS (Billing Per Sample), RPS (Revenue Per Sample), Collection%, Collector status
- **Income Tracking**: Monthly income per account

## API Endpoints

### Development Endpoints (No Authentication Required)
- `GET /api/dashboard/dev/mock-data?period_type={period}` - Get financial summary data
- `GET /api/dashboard/dev/territory-data?period_type={period}` - Get territory performance data
- `GET /api/dashboard/dev/account-data?territory={territory}` - Get account-level data

### Period Types
- `ytd` - Year-to-Date (default)
- `previous_month` - Previous Month
- `current_month` - Current Month
- `qtd` - Quarter-to-Date
- `t12m` - Trailing 12 Months

### Territory Options
- `all` - All territories (default)
- `Alpha`, `Bravo`, `Charlie`, `Delta`, `Echo`, `Foxtrot` - Specific territories

## Data Sources

### Current Implementation
The dashboard currently uses **mock data** for demonstration purposes. The data includes:
- Realistic financial metrics based on typical healthcare laboratory operations
- Territory performance data with 6 territories (Alpha through Foxtrot)
- Account-level data for 8 sample practices
- Monthly revenue trends for the current year

### Future Integration
The dashboard is designed to integrate with:
- **QuickBooks Online**: For real financial data
- **Database**: For historical data and analytics
- **External APIs**: For additional data sources

## Navigation

### Time Period Selector
Use the dropdown in the top-right corner to switch between different time periods:
- Previous Month
- Current Month
- Quarter-to-Date
- Year-to-Date (default)
- Trailing 12 Months

### Section Navigation
Use the navigation tabs to switch between:
- **Company**: Overall company performance
- **Territories**: Territory-level analysis
- **Accounts**: Account-level details

## Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Kill processes using port 5000
   lsof -ti:5000 | xargs kill -9
   
   # Or use a different port
   PORT=5001 python app.py
   ```

2. **Database Connection Issues**
   - The dashboard works with mock data and doesn't require a database
   - For production use, set up PostgreSQL and configure environment variables

3. **Authentication Issues**
   - Development endpoints don't require authentication
   - For production, implement proper JWT authentication

### Browser Compatibility
- Chrome (recommended)
- Firefox
- Safari
- Edge

## Development

### Adding New Data
To add new mock data, modify the endpoints in `app/api/dashboard.py`:
- `get_mock_dashboard_data()` - Financial summary data
- `get_mock_territory_data()` - Territory performance data
- `get_mock_account_data()` - Account-level data

### Customizing Charts
The dashboard uses Chart.js for visualizations. Modify the chart configurations in `static/dashboard.html`.

### Styling
The dashboard uses Bootstrap 5 for styling. Custom CSS can be added to the `<style>` section in `static/dashboard.html`.

## Production Deployment

### Environment Variables
Create a `.env` file with the following variables:
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/account_analysis
DB_HOST=localhost
DB_PORT=5432
DB_NAME=account_analysis
DB_USER=postgres
DB_PASSWORD=your_password

# JWT Authentication
JWT_SECRET_KEY=your_super_secret_jwt_key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Application Settings
FLASK_ENV=production
FLASK_DEBUG=false
FLASK_SECRET_KEY=your_flask_secret_key
PORT=5000
```

### Security Considerations
- Remove development endpoints in production
- Implement proper authentication
- Use HTTPS in production
- Secure database connections
- Validate all user inputs

## Support

For issues or questions:
1. Check the browser console for JavaScript errors
2. Verify the Flask application is running
3. Test API endpoints directly with curl
4. Check the application logs for server-side errors 