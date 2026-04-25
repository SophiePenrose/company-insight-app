import pytest
#!/usr/bin/env python3
"""
Test script for the Revolut Business Prospect Readiness Engine
"""
import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.prospect_pipeline import ProspectAnalysisPipeline
from clients.companies_house import CompaniesHouseClient

@pytest.mark.asyncio
async def test_analysis():
    """Test the prospect analysis pipeline with sample companies"""
    
    # Initialize clients and pipeline
    ch_client = CompaniesHouseClient(api_key="test_key")  # We'll mock this
    pipeline = ProspectAnalysisPipeline(ch_client)
    
    # Test companies (using real company numbers for demonstration)
    test_companies = [
        "04547069",  # A real UK company number (Virgin Media)
        "03033677",  # Another real company (Virgin Media Inc)
    ]
    
    print("🚀 Testing Revolut Business Prospect Readiness Engine")
    print("=" * 60)
    
    for company_number in test_companies:
        print(f"\n📊 Analyzing company {company_number}...")
        try:
            # Run analysis
            report = await pipeline.analyze_company(company_number)
            
            # Display results
            print(f"✅ Analysis complete for {report.company_overview.company_name}")
            print(f"🏢 Industry: {report.company_overview.industry_classification}")
            print(f"💰 Turnover: £{report.company_overview.latest_revenue_gbp or 'Unknown':,.0f}" if report.company_overview.latest_revenue_gbp else f"💰 Turnover: Unknown")
            print(f"🎯 Priority Tier: {report.priority_tier}")
            print(f"⭐ Overall Score: {report.overall_readiness_score:.1f}/100")
            
            print("\n📋 Top Use Cases:")
            for use_case, score in sorted(report.all_use_case_scores.items(), key=lambda x: x[1], reverse=True)[:3]:
                print(f"  • {use_case}: {score:.1f}/100")
            
            print(f"\n🔍 Signals Detected: {len(report.detected_signals)}")
            print(f"🏦 Providers Detected: {len(report.provider_usage)}")
            
            if report.evidenced_pains or report.inferred_pains:
                total_pains = len(report.evidenced_pains) + len(report.inferred_pains)
                print(f"\n💡 Key Pain Points: {total_pains} identified")
                
        except Exception as e:
            print(f"❌ Error analyzing {company_number}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_analysis())
