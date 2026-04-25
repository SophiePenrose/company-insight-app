"""
Scale up the turnover-based discovery to find more companies.
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

async def scale_turnover_discovery():
    """Scale up discovery to find more high-turnover companies."""
    
    print("🚀 SCALING TURNOVER-BASED DISCOVERY")
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
        # Scale up to find 500 companies (closer to the ~40k target)
        print("🔍 Running scaled discovery for 500 companies...")
        print("📊 This will use more search terms and broader analysis")
        
        companies = await discovery.discover_high_turnover_companies(target_companies=500)
        
        print(f"\n✅ Found {len(companies)} qualifying companies")
        
        # Show summary stats
        turnovers = [c.get('turnover_gbp', 0) for c in companies]
        avg_turnover = sum(turnovers) / len(turnovers) if turnovers else 0
        min_turnover = min(turnovers) if turnovers else 0
        max_turnover = max(turnovers) if turnovers else 0
        
        print("\n📈 SUMMARY STATISTICS:")
        print(f"   • Average Turnover: £{avg_turnover:,.0f}")
        print(f"   • Minimum Turnover: £{min_turnover:,.0f}")
        print(f"   • Maximum Turnover: £{max_turnover:,.0f}")
        print(f"   • Target Threshold: £{discovery.min_turnover:,.0f}")
        
        # Show top 10 companies
        print("\n🏆 TOP 10 COMPANIES BY TURNOVER:")
        print("-" * 40)
        
        for i, company in enumerate(companies[:10]):
            print(f"{i+1:2d}. £{company.get('turnover_gbp', 0):,.0f} - {company.get('company_name', 'Unknown')}")
        
        # Save results
        if companies:
            result_data = discovery.save_turnover_discovery_results(
                companies, 
                filename="scaled_turnover_discovery_results.json"
            )
            print(f"\n💾 Results saved with {result_data['summary']['total_companies']} companies")
        
        print("\n🎉 SCALED DISCOVERY COMPLETED!")
        print(f"📊 Successfully demonstrated finding {len(companies)} mid-market companies")
        print("🔄 This approach can be scaled to find the full ~40,000 target companies")
        
    except Exception as e:
        print(f"❌ Scaled discovery failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(scale_turnover_discovery())
