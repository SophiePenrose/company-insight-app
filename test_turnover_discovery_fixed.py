import pytest
"""
Test script for turnover-based company discovery.
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

from src.clients.companies_house import CompaniesHouseClient
from src.services.turnover_based_discovery_fixed import TurnoverBasedDiscovery

@pytest.mark.asyncio
async def test_turnover_discovery():
    """Test the turnover-based discovery system."""
    
    print("🧪 TESTING TURNOVER-BASED DISCOVERY SYSTEM")
    print("=" * 50)
    
    # Initialize client
    api_key = os.getenv("COMPANIES_HOUSE_API_KEY")
    if not api_key:
        print("❌ No COMPANIES_HOUSE_API_KEY found in environment")
        return
    
    ch_client = CompaniesHouseClient(api_key)
    
    # Initialize discovery service
    discovery = TurnoverBasedDiscovery(ch_client)
    
    try:
        # Run discovery for a small sample
        print("🔍 Running discovery for 50 companies...")
        companies = await discovery.discover_high_turnover_companies(target_companies=50)
        
        print(f"\n✅ Found {len(companies)} qualifying companies")
        
        # Show sample results
        print("\n📊 SAMPLE RESULTS:")
        print("-" * 30)
        
        for i, company in enumerate(companies[:5]):  # Show first 5
            print(f"{i+1}. {company.get('company_name', 'Unknown')}")
            print(f"   Company #: {company['company_number']}")
            print(f"   Turnover: £{company.get('turnover_gbp', 0):,.0f}")
            print(f"   Status: {company.get('status', 'Unknown')}")
            print()
        
        # Save results
        if companies:
            result_data = discovery.save_turnover_discovery_results(companies)
            print(f"\n💾 Results saved with {result_data['summary']['total_companies']} companies")
        
        print("\n🎉 TEST COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_turnover_discovery())
