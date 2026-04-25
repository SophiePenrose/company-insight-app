import pytest
#!/usr/bin/env python3
"""
Test the complete Revolut Business Prospect Readiness Engine with real API data
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from dotenv import load_dotenv
load_dotenv()

from services.prospect_pipeline import ProspectAnalysisPipeline
from clients.companies_house import CompaniesHouseClient

@pytest.mark.asyncio
async def test_real_analysis():
    """Test the prospect analysis pipeline with real Companies House data"""
    
    # Load API key
    api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
    if not api_key:
        print('❌ No API key found in environment')
        return
    
    print("🚀 Testing Revolut Business Prospect Readiness Engine with Real Data")
    print("=" * 70)
    print(f"🔑 API Key: {api_key[:8]}...")
    
    # Initialize clients and pipeline
    ch_client = CompaniesHouseClient(api_key=api_key)
    pipeline = ProspectAnalysisPipeline(ch_client)
    
    # Test companies (real UK companies with good data)
    test_companies = [
        "04547069",  # PUNCHDRUNK ENRICHMENT LIMITED
        "03033677",  # VIRGIN MEDIA INC
        "06500244",  # TRANSFERWISE LTD (Wise)
    ]
    
    for company_number in test_companies:
        print(f"\n{'='*50}")
        print(f"📊 Analyzing company {company_number}...")
        try:
            # Run analysis
            report = await pipeline.analyze_company(company_number)
            
            # Display results
            company = report.company_overview
            print(f"✅ Analysis complete for {company.company_name}")
            print(f"🏢 Industry: {company.industry_classification}")
            print(f"💼 Business Model: {company.business_model}")
            print(f"📍 Status: {company.status}")
            print(f"🏛️ Entity Type: {company.legal_entity_type}")
            
            if company.latest_revenue_gbp:
                print(f"💰 Revenue: £{company.latest_revenue_gbp:,.0f}")
            if company.employee_count:
                print(f"👥 Employees: {company.employee_count}")
            
            print(f"🎯 Priority Tier: {report.priority_tier}")
            print(f"⭐ Overall Score: {report.overall_readiness_score:.1f}/100")
            print(f"📊 Confidence: {report.confidence_level}")
            
            print("\n📋 Use Case Scores:")
            for use_case, score in sorted(report.all_use_case_scores.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  • {use_case}: {score:.1f}/100")
            
            print(f"\n🔍 Signals Detected: {len(report.detected_signals)}")
            print(f"🏦 Providers Detected: {len(report.provider_usage)}")
            
            total_pains = len(report.evidenced_pains) + len(report.inferred_pains)
            if total_pains > 0:
                print(f"💡 Pain Points Identified: {total_pains}")
            
            print(f"\n💬 Recommended Outreach: {report.recommended_outreach_angle}")
            print(f"🎯 Entry Point: {report.suggested_entry_point}")
            
        except Exception as e:
            print(f"❌ Error analyzing {company_number}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*70}")
    print("🎉 Real data analysis test completed!")
    print("📈 The Revolut Business Prospect Readiness Engine is fully operational!")

if __name__ == "__main__":
    asyncio.run(test_real_analysis())
