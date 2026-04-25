"""
Test iXBRL API with companies from our discovery results.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.clients.ixbrl_converter import IXBRLConverterClient

def test_with_discovery_companies():
    """Test iXBRL with companies from our discovery."""
    
    print("🧪 TESTING iXBRL WITH COMPANIES FROM DISCOVERY RESULTS")
    print("=" * 50)
    
    # Initialize iXBRL client
    ixbrl_key = os.getenv("IXBRL_API_KEY")
    if not ixbrl_key:
        print("❌ No IXBRL_API_KEY found")
        return
    
    ixbrl_client = IXBRLConverterClient(ixbrl_key)
    
    # Use companies from our earlier discovery results
    test_companies = [
        "13638252",  # LTD AGRI SERVICES LIMITED
        "14174343",  # LIMITED EDITION FASHION LTD
        "14068406",  # LTD CONNECT INTERNATIONAL LIMITED
        "13184160",  # LTD INVESTMENTS LIMITED
        "15646497",  # LIMITED EDITION HOMES LTD
    ]
    
    print("🔍 Testing iXBRL API with discovered companies:\n")
    
    successful = 0
    failed = 0
    
    for company_number in test_companies:
        print(f"Testing company: {company_number}")
        
        try:
            # Get real financial data
            financials = ixbrl_client.get_financials_metadata(company_number)
            
            if financials:
                print(f"  ✅ API Response received")
                
                # Extract turnover
                turnover = ixbrl_client.extract_turnover(financials)
                if turnover:
                    print(f"     💰 Real Turnover: £{turnover:,.0f}")
                    successful += 1
                else:
                    print(f"     ⚠️  Turnover not in response")
                    print(f"     Available fields: {list(financials.keys())[:10]}")
                    failed += 1
            else:
                print(f"  ⚠️  No response from API")
                failed += 1
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed += 1
        
        print()
    
    print(f"\n✅ Test Results: {successful}/{len(test_companies)} successful")
    if successful > 0:
        print("🎉 iXBRL API is working and returning real financial data!")
    else:
        print("⚠️  iXBRL API not returning turnover data - may need different API version or endpoint")

if __name__ == "__main__":
    test_with_discovery_companies()
