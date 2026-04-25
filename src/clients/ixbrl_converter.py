"""
Client for Convert iXBRL API.
Converts company filing data to structured financial data.
"""

import requests
from typing import Dict, Any, Optional

class IXBRLConverterClient:
    """
    Client for Convert iXBRL API.
    Provides access to parsed financial data from company filings.
    """
    
    BASE_URL = "https://convert-ixbrl.co.uk/api"
    
    def __init__(self, api_key: str):
        """Initialize with API key."""
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "User-Agent": "CompanyInsightApp/1.0"
        })
    
    def get_financials_metadata(self, company_number: str) -> Optional[Dict[str, Any]]:
        """
        Get financial metadata for a company using iXBRL conversion.
        
        Args:
            company_number: UK Companies House company number (8 digits)
            
        Returns:
            Dict with financial metadata including turnover, or None if error
        """
        try:
            url = f"{self.BASE_URL}/financialsMetaData"
            params = {
                "companyNumber": company_number,
                "apiVersion": "2"
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return None
    
    def extract_turnover(self, financials: Dict[str, Any]) -> Optional[float]:
        """
        Extract turnover/revenue from financial metadata.
        
        Args:
            financials: Financial metadata from iXBRL API
            
        Returns:
            Turnover in GBP as float, or None if not found
        """
        if not financials:
            return None
        
        # Try common field names for turnover/revenue
        turnover_fields = [
            'turnover',
            'revenue', 
            'sales',
            'operatingRevenue',
            'totalRevenue',
            'grossRevenue'
        ]
        
        for field in turnover_fields:
            if field in financials:
                value = financials[field]
                if isinstance(value, (int, float)) and value > 0:
                    return float(value)
        
        # Try nested structures
        if 'profitAndLoss' in financials:
            pl = financials['profitAndLoss']
            if isinstance(pl, dict):
                for field in turnover_fields:
                    if field in pl:
                        value = pl[field]
                        if isinstance(value, (int, float)) and value > 0:
                            return float(value)
        
        return None
    
    def get_company_turnover(self, company_number: str) -> Optional[float]:
        """
        Convenience method: Get company turnover directly.
        
        Args:
            company_number: UK Companies House company number
            
        Returns:
            Turnover in GBP, or None if not available
        """
        financials = self.get_financials_metadata(company_number)
        return self.extract_turnover(financials)
