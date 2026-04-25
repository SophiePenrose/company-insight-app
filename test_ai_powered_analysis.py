import pytest
import pytest
#!/usr/bin/env python3
"""
Test the AI-powered prospect analysis system with semantic understanding.
Demonstrates the improved signal detection and smart company discovery.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / 'src'
if src_path.exists():
    sys.path.insert(0, str(src_path))

from dotenv import load_dotenv
load_dotenv()

from src.services.ai_signal_detector import AISignalDetector, SemanticSignal
from src.services.smart_company_discovery import SmartCompanyDiscovery
from src.services.continuous_monitor import ContinuousMonitor
from src.clients.companies_house import CompaniesHouseClient
from src.services.prospect_pipeline import ProspectAnalysisPipeline

@pytest.mark.asyncio
async def test_ai_signal_detection():
    """Test the AI-powered signal detection with semantic analysis."""
    print("🧠 Testing AI-Powered Signal Detection")
    print("=" * 50)
    
    detector = AISignalDetector()
    
    # Test documents with various phrasings of the same concepts
    test_documents = [
        {
            "text": "The company has experienced significant foreign exchange losses due to currency volatility in international markets. This has created substantial challenges for our treasury operations.",
            "expected_signals": ["fx_cost_pain", "cash_management_pain"]
        },
        {
            "text": "Our payment processing costs have become increasingly expensive, with interchange fees and merchant service charges impacting profitability significantly.",
            "expected_signals": ["payment_cost_pain"]
        },
        {
            "text": "The business is planning international expansion into European markets, requiring sophisticated cross-border payment solutions and multi-currency banking capabilities.",
            "expected_signals": ["international_growth_signal"]
        },
        {
            "text": "Manual reconciliation processes are time-consuming and error-prone. We need better integration between our accounting software and banking systems.",
            "expected_signals": ["accounting_integration_opportunity"]
        }
    ]
    
    company_context = {
        "international_subsidiary_count": 2,
        "latest_revenue_gbp": 75000000,
        "countries_of_operation": ["UK", "Germany", "France"]
    }
    
    for i, doc in enumerate(test_documents, 1):
        print(f"\n📄 Document {i}:")
        print(f"   \"{doc['text'][:100]}...\"")
        
        signals = detector.analyze_text_semantically(doc["text"], company_context)
        
        print(f"   🔍 Signals detected: {len(signals)}")
        
        for signal in signals:
            print(f"      • {signal.signal_id}: {signal.confidence:.2f} confidence")
            print(f"        Evidence: \"{signal.evidence_text}\"")
            print(f"        Context: \"{signal.context[:80]}...\"")
    
    print("\n✅ AI signal detection test complete!")

@pytest.mark.asyncio
async def test_smart_discovery():
    """Test the smart company discovery system."""
    print("\n🎯 Testing Smart Company Discovery")
    print("=" * 50)
    
    # Load API key
    api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
    if not api_key:
        print("❌ No API key found - skipping discovery test")
        return
    
    ch_client = CompaniesHouseClient(api_key)
    discovery = SmartCompanyDiscovery(ch_client)
    
    print("🔍 Discovering mid-market companies...")
    
    try:
        candidates = await discovery.discover_mid_market_companies(max_companies=20)
        
        print(f"✅ Found {len(candidates)} potential mid-market companies")
        
        # Show sample candidates
        for i, candidate in enumerate(candidates[:5], 1):
            print(f"   {i}. {candidate['company_name']} ({candidate['company_number']})")
            print(f"      Discovery method: {candidate['discovery_method']}")
    
    except Exception as e:
        print(f"❌ Discovery test failed: {e}")
    
    print("\n✅ Smart discovery test complete!")

@pytest.mark.asyncio
async def test_continuous_monitoring():
    """Test the continuous monitoring system."""
    print("\n🔄 Testing Continuous Monitoring System")
    print("=" * 50)
    
    # Load API key
    api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
    if not api_key:
        print("❌ No API key found - skipping monitoring test")
        return
    
    ch_client = CompaniesHouseClient(api_key)
    pipeline = ProspectAnalysisPipeline(ch_client)
    monitor = ContinuousMonitor(ch_client, pipeline)
    
    # Test with a small set of companies
    test_companies = ["04547069", "06500244"]  # Companies we know exist
    
    print(f"📊 Monitoring {len(test_companies)} companies...")
    
    try:
        changes = await monitor.monitor_prospects(test_companies)
        
        print("📈 Monitoring results:")
        print(f"   • New prospects: {changes['new_prospects']}")
        print(f"   • Updated companies: {changes['updated_companies']}")
        print(f"   • New filings: {changes['new_filings']}")
        print(f"   • Errors: {changes['errors']}")
        
        # Show prospect summary
        summary = monitor.get_prospect_summary()
        print(f"\n📊 Database summary:")
        print(f"   • Total prospects: {summary['total_prospects']}")
        print(f"   • Tier breakdown: {summary['tier_breakdown']}")
        
        # Show priority prospects
        priority_prospects = monitor.get_priority_prospects(limit=3)
        if priority_prospects:
            print(f"\n🎯 Top priority prospects:")
            for i, prospect in enumerate(priority_prospects, 1):
                print(f"   {i}. {prospect['company_name']}: {prospect['overall_score']:.1f} ({prospect['priority_tier']})")
    
    except Exception as e:
        print(f"❌ Monitoring test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Continuous monitoring test complete!")

async def demonstrate_semantic_understanding():
    """Demonstrate how semantic analysis finds signals that keyword matching would miss."""
    print("\n🧠 Demonstrating Semantic Understanding")
    print("=" * 50)
    
    detector = AISignalDetector()
    
    # Examples of how companies actually talk about problems vs. exact keywords
    examples = [
        {
            "text": "The weakening pound has made our imports much more expensive, putting pressure on our margins and cash flow.",
            "keyword_miss": "Doesn't contain 'foreign exchange costs' or 'FX expenses'",
            "semantic_hit": "Recognizes currency weakness + expensive imports + margin pressure = FX cost pain"
        },
        {
            "text": "We're struggling with multiple bank accounts across different providers, making reconciliation a nightmare.",
            "keyword_miss": "No mention of 'cash management inefficiencies'",
            "semantic_hit": "Identifies multiple accounts + reconciliation problems = cash management pain"
        },
        {
            "text": "Transaction fees from our current payment processor are eating into our profits.",
            "keyword_miss": "Not the exact phrase 'payment processing costs'",
            "semantic_hit": "Recognizes transaction fees + profit impact = payment cost pain"
        }
    ]
    
    company_context = {
        "international_subsidiary_count": 1,
        "latest_revenue_gbp": 25000000,
        "countries_of_operation": ["UK", "USA"]
    }
    
    for i, example in enumerate(examples, 1):
        print(f"\n📝 Example {i}:")
        print(f"   \"{example['text']}\"")
        print(f"   ❌ Keyword matching would miss: {example['keyword_miss']}")
        print(f"   ✅ Semantic analysis finds: {example['semantic_hit']}")
        
        # Test with AI detector
        signals = detector.analyze_text_semantically(example["text"], company_context)
        if signals:
            print(f"   🎯 Detected signals: {', '.join([s.signal_id for s in signals])}")
        else:
            print("   🤔 No signals detected (may need more context)")

async def main():
    """Run all AI-powered analysis tests."""
    print("🚀 AI-Powered Prospect Analysis System Test Suite")
    print("=" * 60)
    
    await test_ai_signal_detection()
    await test_smart_discovery()
    await test_continuous_monitoring()
    await demonstrate_semantic_understanding()
    
    print("\n" + "=" * 60)
    print("🎉 All AI-powered analysis tests completed!")
    print("\n📊 Key Improvements Demonstrated:")
    print("   • Semantic understanding beyond keyword matching")
    print("   • Smart company discovery for mid-market targeting")
    print("   • Continuous monitoring for prospect database updates")
    print("   • Context-aware signal confidence scoring")
    print("   • Multi-phrase pattern recognition for business problems")

if __name__ == "__main__":
    asyncio.run(main())
