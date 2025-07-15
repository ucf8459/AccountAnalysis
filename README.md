# Account Analysis Dashboard

A comprehensive financial analytics dashboard for analyzing account and territory performance, with integration to QuickBooks Online and advanced collection percentage calculations.

## Features

- **Financial Analytics Dashboard**: Real-time analysis of revenue, COGS, profit, and per-sample metrics
- **Collection Percentage Analysis**: Historical collection percentage calculations with weighted averages
- **Territory Performance Tracking**: Territory-based performance metrics and comparisons
- **QuickBooks Online Integration**: Seamless integration with QBO for financial data
- **Interactive Data Tables**: Sortable and filterable account tables with dynamic totals
- **Collector Cost Management**: Track and manage collector costs per practice
- **Financial Class Breakdown**: Detailed payer mix analysis by practice

## Key Metrics

- **RPS (Revenue Per Sample)**: Average revenue generated per sample
- **BPS (Billing Per Sample)**: Average billing amount per sample
- **PPS (Profit Per Sample)**: Average profit generated per sample
- **CPS (Cost Per Sample)**: Average cost per sample (expenses only)
- **Delta**: Difference between PPS and CPS
- **Collection Percentage**: Historical average collection rate

## Technology Stack

- **Backend**: Python Flask with PostgreSQL
- **Frontend**: HTML, CSS, JavaScript with Bootstrap
- **Charts**: Chart.js for data visualization
- **Database**: PostgreSQL with advanced analytics schemas
- **Authentication**: JWT-based authentication
- **ETL**: Custom scripts for data processing

## Installation

### Prerequisites

- Python 3.8+
- PostgreSQL 12+
- Node.js (for package management)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AccountAnalysis
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies** (if any)
   ```bash
   npm install
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your database credentials and API keys
   ```

5. **Set up the database**
   ```bash
   python setup_database_simple.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5001`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
DB_NAME=healthtech
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
QBO_CLIENT_ID=your_qbo_client_id
QBO_CLIENT_SECRET=your_qbo_client_secret
QBO_REDIRECT_URI=http://localhost:5001/api/qbo/callback
```

### Database Setup

The application uses PostgreSQL with the following main schemas:
- `public`: Core application data
- `staging`: Data import and processing
- `analytics`: Aggregated dashboard data

## Usage

### Dashboard Overview

Access the main dashboard at `/dashboard` to view:
- Financial summary by period
- Territory performance metrics
- Account KPIs and trends

### Account Table

The account table (`/account-table`) provides:
- Practice-level financial metrics
- Sortable columns for all metrics
- Dynamic filtering and totals
- Collection percentage analysis
- Collector cost management

### Data Import

Use the ETL scripts in the `scripts/` directory to import:
- Account data from Excel files
- Sample billing information
- Practice and territory mappings
- COGS and expense data

## API Endpoints

### Dashboard
- `GET /api/dashboard/account-table-live` - Live account data
- `GET /api/dashboard/financial-summary` - Financial summary
- `GET /api/dashboard/territory-performance` - Territory metrics

### Account Management
- `POST /api/dashboard/update-collector` - Update collector status
- `POST /api/dashboard/update-collector-cost` - Update collector cost
- `GET /api/dashboard/financial-class-breakdown` - Payer mix analysis

### QBO Integration
- `GET /api/qbo/authorize` - QBO authorization
- `GET /api/qbo/callback` - OAuth callback
- `GET /api/qbo/integrated-data` - QBO data retrieval

## Data Models

### Core Tables
- `account_data`: Practice and account information
- `sample_billing`: Sample billing and payment data
- `cogs_expense`: COGS and expense tracking
- `practice_samples`: Sample tracking by practice

### Analytics Tables
- `analytics.financial_summary`: Aggregated financial data
- `analytics.territory_performance`: Territory performance metrics

## Development

### Project Structure
```
AccountAnalysis/
├── app/                    # Flask application
│   ├── api/               # API endpoints
│   ├── models/            # Data models
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── database/              # Database schemas and migrations
├── scripts/               # ETL and setup scripts
├── static/                # Static assets
├── templates/             # HTML templates
└── tests/                 # Test files
```

### Running Tests
```bash
python -m pytest tests/
```

### Code Style
The project follows PEP 8 guidelines. Use a linter like `flake8` or `black` for code formatting.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

For support and questions, please contact the development team or create an issue in the repository. 