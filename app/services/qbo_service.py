"""
QuickBooks Online (QBO) service for data extraction and API interactions.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from intuitlib.client import AuthClient
from intuitlib.enums import Scopes
from dotenv import load_dotenv

load_dotenv()

class QBOService:
    """Service class for QuickBooks Online API interactions."""
    
    def __init__(self):
        self.client_id = os.getenv('QBO_CLIENT_ID')
        self.client_secret = os.getenv('QBO_CLIENT_SECRET')
        self.environment = os.getenv('QBO_ENVIRONMENT', 'sandbox')
        self.redirect_uri = os.getenv('QBO_REDIRECT_URI')
        
        if not all([self.client_id, self.client_secret, self.redirect_uri]):
            raise ValueError("Missing required QBO environment variables")
        
        self.oauth_client = AuthClient(
            client_id=self.client_id,
            client_secret=self.client_secret,
            environment=self.environment,
            redirect_uri=self.redirect_uri
        )
        
        self.base_url = 'https://sandbox-accounts.platform.intuit.com' if self.environment == 'sandbox' else 'https://accounts.platform.intuit.com'
        self.api_url = 'https://sandbox-quickbooks.api.intuit.com' if self.environment == 'sandbox' else 'https://quickbooks.api.intuit.com'
    
    def get_authorization_url(self) -> str:
        """Get the authorization URL for OAuth flow."""
        scopes = [
            Scopes.ACCOUNTING,
            Scopes.OPENID,
            Scopes.EMAIL,
            Scopes.PROFILE
        ]
        
        auth_url = self.oauth_client.get_authorization_url(scopes)
        return auth_url
    
    def exchange_code_for_tokens(self, auth_code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens."""
        try:
            tokens = self.oauth_client.get_bearer_token(auth_code, realm_id=None)
            return {
                'access_token': tokens.access_token,
                'refresh_token': tokens.refresh_token,
                'realm_id': tokens.realm_id,
                'expires_at': tokens.expires_at.isoformat() if tokens.expires_at else None
            }
        except Exception as e:
            raise Exception(f"Failed to exchange code for tokens: {str(e)}")
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh the access token using refresh token."""
        try:
            self.oauth_client.refresh(refresh_token)
            return {
                'access_token': self.oauth_client.access_token,
                'refresh_token': self.oauth_client.refresh_token,
                'expires_at': self.oauth_client.token_endpoint.expires_at.isoformat() if self.oauth_client.token_endpoint.expires_at else None
            }
        except Exception as e:
            raise Exception(f"Failed to refresh access token: {str(e)}")
    
    def _make_api_request(self, endpoint: str, access_token: str, realm_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to the QBO API."""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.api_url}/v3/company/{realm_id}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"QBO API request failed: {str(e)}")
    
    def get_company_info(self, access_token: str, realm_id: str) -> Dict[str, Any]:
        """Get company information."""
        return self._make_api_request('companyinfo', access_token, realm_id)
    
    def get_accounts(self, access_token: str, realm_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Get accounts from QBO."""
        return self._make_api_request('query', access_token, realm_id, {
            'query': 'SELECT * FROM Account',
            **(params or {})
        })
    
    def get_customers(self, access_token: str, realm_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Get customers from QBO."""
        return self._make_api_request('query', access_token, realm_id, {
            'query': 'SELECT * FROM Customer',
            **(params or {})
        })
    
    def get_invoices(self, access_token: str, realm_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get invoices from QBO with optional date filtering."""
        query = 'SELECT * FROM Invoice'
        if start_date and end_date:
            query += f" WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        elif start_date:
            query += f" WHERE TxnDate >= '{start_date}'"
        elif end_date:
            query += f" WHERE TxnDate <= '{end_date}'"
        
        return self._make_api_request('query', access_token, realm_id, {'query': query})
    
    def get_bills(self, access_token: str, realm_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get bills from QBO with optional date filtering."""
        query = 'SELECT * FROM Bill'
        if start_date and end_date:
            query += f" WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        elif start_date:
            query += f" WHERE TxnDate >= '{start_date}'"
        elif end_date:
            query += f" WHERE TxnDate <= '{end_date}'"
        
        return self._make_api_request('query', access_token, realm_id, {'query': query})
    
    def get_sales_receipts(self, access_token: str, realm_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get sales receipts from QBO with optional date filtering."""
        query = 'SELECT * FROM SalesReceipt'
        if start_date and end_date:
            query += f" WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'"
        elif start_date:
            query += f" WHERE TxnDate >= '{start_date}'"
        elif end_date:
            query += f" WHERE TxnDate <= '{end_date}'"
        
        return self._make_api_request('query', access_token, realm_id, {'query': query})
    
    def get_financial_summary(self, access_token: str, realm_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get financial summary data for the specified period."""
        try:
            # Get invoices (revenue)
            invoices = self.get_invoices(access_token, realm_id, start_date, end_date)
            
            # Get bills (expenses)
            bills = self.get_bills(access_token, realm_id, start_date, end_date)
            
            # Calculate totals
            total_revenue = sum(
                float(invoice.get('TotalAmt', 0)) 
                for invoice in invoices.get('QueryResponse', {}).get('Invoice', [])
            )
            
            total_expenses = sum(
                float(bill.get('TotalAmt', 0)) 
                for bill in bills.get('QueryResponse', {}).get('Bill', [])
            )
            
            gross_profit = total_revenue - total_expenses
            
            return {
                'period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'revenue': total_revenue,
                'expenses': total_expenses,
                'gross_profit': gross_profit,
                'net_profit': gross_profit,  # Simplified for now
                'invoice_count': len(invoices.get('QueryResponse', {}).get('Invoice', [])),
                'bill_count': len(bills.get('QueryResponse', {}).get('Bill', []))
            }
            
        except Exception as e:
            raise Exception(f"Failed to get financial summary: {str(e)}")
    
    def get_monthly_revenue(self, access_token: str, realm_id: str, year: int) -> List[Dict[str, Any]]:
        """Get monthly revenue data for a specific year."""
        monthly_data = []
        
        for month in range(1, 13):
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year}-{month:02d}-31"
            else:
                end_date = f"{year}-{month+1:02d}-01"
            
            try:
                invoices = self.get_invoices(access_token, realm_id, start_date, end_date)
                total_revenue = sum(
                    float(invoice.get('TotalAmt', 0)) 
                    for invoice in invoices.get('QueryResponse', {}).get('Invoice', [])
                )
                
                monthly_data.append({
                    'month': month,
                    'month_name': datetime(year, month, 1).strftime('%b'),
                    'revenue': total_revenue,
                    'invoice_count': len(invoices.get('QueryResponse', {}).get('Invoice', []))
                })
                
            except Exception as e:
                # If there's an error for a specific month, add zero values
                monthly_data.append({
                    'month': month,
                    'month_name': datetime(year, month, 1).strftime('%b'),
                    'revenue': 0,
                    'invoice_count': 0
                })
        
        return monthly_data
    
    def get_bills_by_gl_codes(self, access_token: str, realm_id: str, gl_codes: list, start_date: str, end_date: str) -> dict:
        print('[DEBUG] Entered get_bills_by_gl_codes')
        # Build the IN clause for GL codes
        gl_codes_str = ','.join([f"'{code}'" for code in gl_codes])
        query = f"""
            SELECT * FROM Bill
            WHERE TxnDate >= '{start_date}' AND TxnDate <= '{end_date}'
              AND AccountRef IN ({gl_codes_str})
        """
        print(f"[DEBUG] QBO Bill Query: {query}")
        try:
            bills = self._make_api_request('query', access_token, realm_id, {'query': query})
        except Exception as e:
            print(f'[DEBUG] QBO API Exception: {e}')
            return {}
        bill_list = bills.get('QueryResponse', {}).get('Bill', [])
        print(f"[DEBUG] Number of bills returned: {len(bill_list)}")
        if not bill_list:
            print('[DEBUG] No QBO bills found for the given period and GL codes.')
        # Group and sum by territory (assuming territory is a custom field or memo)
        territory_totals = {}
        for bill in bill_list:
            # Debug: print class and territory fields
            print('[DEBUG] Bill:', json.dumps(bill, indent=2))
            territory = None
            # Try to extract territory from a custom field or memo
            if 'CustomField' in bill and bill['CustomField']:
                for field in bill['CustomField']:
                    if field.get('Name', '').lower() == 'territory':
                        territory = field.get('StringValue')
                        break
            if not territory and 'PrivateNote' in bill:
                territory = bill['PrivateNote']
            # Try to extract class (QBO class)
            qbo_class = bill.get('ClassRef', {}).get('name') if bill.get('ClassRef') else None
            print(f"[DEBUG] QBO Class: {qbo_class}, Territory: {territory}")
            if not territory and qbo_class:
                territory = qbo_class
            if not territory:
                territory = 'Unknown'
            total_amt = float(bill.get('TotalAmt', 0))
            territory_totals[territory] = territory_totals.get(territory, 0) + total_amt
        print('[DEBUG] COGS by territory:', territory_totals)
        return territory_totals 