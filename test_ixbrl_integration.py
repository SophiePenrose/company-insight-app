"""
Test the iXBRL API integration with real company data.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.clients.ixbrl_converter import IXBRLConverterClient

def test_ixbrl_api():
    """Test iXBRL API with real companies."""
    
    print("🧪 TESTING iXBRL API INTEGRATION")
    print("=" * 50)
    
    # Initialize iXBRL client
    ixbrl_key = os.getenv("IXBRL_API_KEY")
    if not ixbrl_key:
        print("❌ No IXBRL_API_KEY found in environment")
        return
    
    ixbrl_client = IXBRLConverterClient(ixbrl_key)
    
    # Test with some well-known UK companies
    # Using some common company registration numbers
    test_companies = [
        ("00000001", "BP p.l.c."),  # BP
        ("00000002", "Shell UK"),
        ("02374868", "Google UK"),  # Example - may not work if not in test DB
    ]
    
    print("🔍 Testing iXBRL API with real companies:\n")
    
    for company_number, company_name in test_companies:
        print(f"Testing: {company_name} ({company_number})")
        
        try:
            # Get financial metadata
            financials = ixbrl_client.get_financials_metadata(company_number)
            
            if financials:
                print(f"  ✅ API Response received")
                print(f"     Keys: {list(financials.keys())[:5]}...")
                
                # Try to extract turnover
                turnover = ixbrl_client.extract_turnover(financials)
                if turnover:
                    print(f"     💰 Turnover: £{turnover:,.0f}")
                else:
                    print(f"     ⚠️  No turnover field found")
            else:
                print(f"  ⚠️  No data returned (company may not have filed)")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        print()
    
    print("✅ iXBRL API test completed")

if __name__ == "__main__":
    test_ixbrl_api()
