# QuickBooks Online Integration Setup

This guide will help you set up the QuickBooks Online (QBO) integration for the Account Analysis dashboard.

## Prerequisites

1. **QuickBooks Online Account**: You need a QBO account (sandbox or production)
2. **PostgreSQL Database**: Running and accessible
3. **Python Environment**: With all dependencies installed

## Step 1: QuickBooks Developer Account Setup

### 1.1 Create a QuickBooks Developer Account
1. Go to [Intuit Developer](https://developer.intuit.com/)
2. Sign up for a free developer account
3. Create a new app for QuickBooks Online

### 1.2 Configure Your App
1. In your app settings, note down:
   - **Client ID**
   - **Client Secret**
   - **Environment** (sandbox or production)

2. Set the **Redirect URI** to:
   ```
   http://localhost:5000/api/qbo/auth/callback
   ```

### 1.3 Environment Configuration
Copy `env.example` to `.env` and update the QBO settings:

```bash
# QuickBooks Online API
QBO_CLIENT_ID=your_qbo_client_id_here
QBO_CLIENT_SECRET=your_qbo_client_secret_here
QBO_ENVIRONMENT=sandbox  # or production
QBO_REDIRECT_URI=http://localhost:5000/api/qbo/auth/callback
```

## Step 2: Database Setup

### 2.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 2.2 Run Setup Script
```bash
python setup_qbo.py
```

This script will:
- Check environment variables
- Test database connection
- Setup database schema
- Test QBO service initialization

## Step 3: Start the Application

### 3.1 Start Flask App
```bash
python app.py
```

### 3.2 Access the Application
1. **Authentication Page**: http://localhost:5000/auth
2. **Dashboard**: http://localhost:5000/dashboard

## Step 4: QuickBooks Authentication

### 4.1 Login
1. Use demo credentials: `admin` / `password123`
2. Click "Login"

### 4.2 Connect QuickBooks
1. Click "Connect QuickBooks Online"
2. You'll be redirected to QuickBooks
3. Authorize the application
4. You'll be redirected back to the dashboard

## Step 5: View Real Data

Once authenticated, the dashboard will:
- Show real financial data from your QBO account
- Update based on the selected time period (YTD, Previous Month, etc.)
- Display monthly revenue and income charts
- Show territory and account performance

## API Endpoints

### QBO Authentication
- `GET /api/qbo/auth/url` - Get QBO authorization URL
- `GET /api/qbo/auth/callback` - Handle OAuth callback

### QBO Data
- `GET /api/qbo/company-info` - Get company information
- `GET /api/qbo/financial-summary` - Get financial summary for period
- `GET /api/qbo/monthly-revenue` - Get monthly revenue data
- `GET /api/qbo/customers` - Get customer list

### Dashboard Integration
- `GET /api/dashboard/qbo-integrated` - Get dashboard data with QBO integration

## Troubleshooting

### Common Issues

1. **"Missing required environment variables"**
   - Ensure all QBO variables are set in `.env`
   - Check that the file is named correctly (`.env`, not `env`)

2. **"Database connection failed"**
   - Verify PostgreSQL is running
   - Check `DATABASE_URL` in `.env`
   - Ensure database exists

3. **"QBO service initialization failed"**
   - Check QBO credentials
   - Verify redirect URI matches exactly
   - Ensure environment is set correctly (sandbox/production)

4. **"No QBO connection found"**
   - Complete the OAuth flow first
   - Check that tokens are stored in database
   - Try re-authenticating

### Debug Mode
Enable debug mode in `.env`:
```
FLASK_DEBUG=true
```

### Logs
Check the console output for detailed error messages.

## Security Notes

1. **Never commit `.env` files** to version control
2. **Use strong secrets** for production
3. **Rotate tokens** regularly
4. **Monitor API usage** to stay within limits

## Production Deployment

For production:
1. Set `QBO_ENVIRONMENT=production`
2. Update redirect URI to your production domain
3. Use HTTPS for all endpoints
4. Set up proper SSL certificates
5. Configure proper logging and monitoring

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the console logs
3. Verify your QBO app configuration
4. Test with sandbox environment first 