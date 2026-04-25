"""
Turnover-based company discovery using real financial data from iXBRL API.
Finds active companies with £15M+ turnover by analyzing actual filed accounts.
"""

import asyncio
import json
import re
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

from src.clients.companies_house import CompaniesHouseClient
from src.clients.ixbrl_converter import IXBRLConverterClient

class TurnoverDiscoveryWithIXBRL:
    """
    High-accuracy system for finding active companies with £15M+ turnover.
    Uses real financial data from iXBRL API instead of estimates.
    """
    
    def __init__(self, ch_client: CompaniesHouseClient, ixbrl_client: IXBRLConverterClient):
        self.ch_client = ch_client
        self.ixbrl_client = ixbrl_client
        
        # Turnover criteria
        self.min_turnover = 15_000_000  # £15M
        
        # Search parameters for broad discovery
        self.broad_search_terms = [
            "limited", "ltd", "services", "solutions", "systems",
            "international", "global", "group", "holdings", "corporation",
            "enterprises", "trading", "professional", "management", "consulting"
        ]
        
        # Filing analysis parameters
        self.recent_accounts_window = 365 * 2  # 2 years
        self.max_filings_to_check = 50
    
    async def discover_high_turnover_companies(self, target_companies: int = 100) -> List[Dict[str, Any]]:
        """
        Discover active companies with £15M+ turnover using real financial data.
        """
        print("💰 DISCOVERING HIGH-TURNOVER COMPANIES (USING REAL iXBRL DATA)")
        print(f"🎯 Target: {target_companies} active companies with £{self.min_turnover:,}+ turnover")
        print("📊 Strategy: Broad search → Active filter → Real financial data analysis (iXBRL)")
        print()
        
        qualified_companies = []
        processed_companies = set()
        
        # Phase 1: Broad discovery of active companies
        print("🔍 Phase 1: Broad company discovery...")
        candidate_batches = await self._broad_company_search(target_companies * 3)
        
        print(f"📋 Found {len(candidate_batches)} candidate batches to analyze")
        
        # Phase 2: Analyze using real financial data from iXBRL
        print("💳 Phase 2: Fetching real financial data from iXBRL API...")
        
        for batch_idx, batch in enumerate(candidate_batches):
            if len(qualified_companies) >= target_companies:
                break
                
            print(f"📊 Processing batch {batch_idx + 1}/{len(candidate_batches)} ({len(batch)} companies)")
            
            batch_qualifiers = await self._analyze_batch_with_ixbrl(batch, processed_companies)
            qualified_companies.extend(batch_qualifiers)
            
            print(f"   ✅ Found {len(batch_qualifiers)} qualifying companies in this batch")
            print(f"   📈 Running total: {len(qualified_companies)} companies")
            
            await asyncio.sleep(0.5)
        
        # Remove duplicates and sort by turnover
        unique_companies = self._deduplicate_by_turnover(qualified_companies)
        sorted_companies = sorted(unique_companies, key=lambda x: x.get('turnover_gbp', 0), reverse=True)
        
        final_companies = sorted_companies[:target_companies]
        
        print("\n✅ DISCOVERY COMPLETE!")
        print(f"🏆 Found {len(final_companies)} active companies with £{self.min_turnover:,}+ turnover")
        print("📊 All turnover figures from real iXBRL financial data")
        
        return final_companies
    
    async def _broad_company_search(self, total_candidates: int) -> List[List[Dict[str, Any]]]:
        """Perform broad searches to find active companies."""
        batches = []
        candidates_per_batch = 100
        
        for term in self.broad_search_terms[:5]:  # Use more search terms
            try:
                results = self.ch_client.search_companies(
                    query=term,
                    items_per_page=min(candidates_per_batch, 100),
                    start_index=0
                )
                
                candidates = []
                for item in results.get("items", []):
                    if self._is_active_company(item):
                        candidates.append({
                            "company_number": item["company_number"],
                            "company_name": item.get("title", ""),
                            "search_term": term,
                            "status": item.get("company_status", ""),
                            "incorporation_date": item.get("date_of_creation")
                        })
                
                if candidates:
                    batches.append(candidates)
                    print(f"   • '{term}': {len(candidates)} active companies")
                
                if len(batches) * candidates_per_batch >= total_candidates:
                    break
                    
            except Exception as e:
                print(f"   • '{term}': Error - {e}")
                continue
        
        return batches
    
    def _is_active_company(self, company_item: Dict[str, Any]) -> bool:
        """Check if company is active."""
        status = company_item.get("company_status", "").lower()
        return status == "active"
    
    async def _analyze_batch_with_ixbrl(self, batch: List[Dict[str, Any]], 
                                       processed: Set[str]) -> List[Dict[str, Any]]:
        """Analyze a batch using real iXBRL financial data."""
        qualifiers = []
        
        for company in batch:
            company_number = company["company_number"]
            
            # Skip if already processed
            if company_number in processed:
                continue
                
            processed.add(company_number)
            
            try:
                # Get company profile
                profile = self.ch_client.company_profile(company_number)
                
                # Skip if not active
                if profile.get("company_status", "").lower() != "active":
                    continue
                
                # 🔑 KEY: Use real iXBRL financial data instead of estimates
                turnover_gbp = self.ixbrl_client.get_company_turnover(company_number)
                
                if turnover_gbp and turnover_gbp >= self.min_turnover:
                    # Also get filing info for context
                    filings = self.ch_client.filing_history(
                        company_number, 
                        items_per_page=5
                    )
                    
                    # Find most recent accounts filing
                    most_recent_accounts = None
                    for filing in filings.get("items", []):
                        if "accounts" in filing.get("description", "").lower():
                            most_recent_accounts = filing
                            break
                    
                    qualified_company = {
                        **company,
                        "turnover_gbp": turnover_gbp,
                        "accounts_filing_date": most_recent_accounts.get("date") if most_recent_accounts else None,
                        "accounts_type": most_recent_accounts.get("description", "") if most_recent_accounts else None,
                        "confidence_level": "high",  # high confidence - real data!
                        "data_source": "iXBRL_API",
                        "analysis_date": datetime.now().isoformat(),
                        "qualification_method": "ixbrl_real_financial_data"
                    }
                    qualifiers.append(qualified_company)
                    
            except Exception as e:
                # Skip companies we can't analyze
                continue
        
        return qualifiers
    
    def _deduplicate_by_turnover(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicates, keeping highest turnover entry."""
        seen = {}
        
        for company in companies:
            company_number = company["company_number"]
            turnover = company.get("turnover_gbp", 0)
            
            if company_number not in seen or turnover > seen[company_number].get("turnover_gbp", 0):
                seen[company_number] = company
        
        return list(seen.values())
    
    def save_results(self, companies: List[Dict[str, Any]], 
                    filename: str = "ixbrl_discovery_results.json"):
        """Save discovery results."""
        output_path = Path("output") / filename
        output_path.parent.mkdir(exist_ok=True)
        
        # Calculate summary stats
        turnovers = [c.get("turnover_gbp", 0) for c in companies]
        avg_turnover = sum(turnovers) / len(turnovers) if turnovers else 0
        min_turnover = min(turnovers) if turnovers else 0
        max_turnover = max(turnovers) if turnovers else 0
        
        result_data = {
            "discovery_date": datetime.now().isoformat(),
            "data_source": "iXBRL_API",
            "confidence_level": "high",
            "criteria": {
                "min_turnover_gbp": self.min_turnover,
                "company_status": "active",
                "financial_data_source": "Real iXBRL conversion API"
            },
            "summary": {
                "total_companies": len(companies),
                "average_turnover_gbp": avg_turnover,
                "min_turnover_gbp": min_turnover,
                "max_turnover_gbp": max_turnover
            },
            "companies": companies
        }
        
        with output_path.open("w") as f:
            json.dump(result_data, f, indent=2)
        
        print(f"💾 Saved {len(companies)} companies to {output_path}")
        
        return result_data
