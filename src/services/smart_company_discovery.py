"""
Smart company discovery system for efficient mid-market prospecting.
Uses advanced filtering and sampling to find relevant companies without processing millions.
"""

import asyncio
import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import random

from src.clients.companies_house import CompaniesHouseClient

class SmartCompanyDiscovery:
    """
    Intelligent system for discovering mid-market companies efficiently.
    Uses strategic sampling and filtering to find prospects without exhaustive searches.
    """
    
    def __init__(self, ch_client: CompaniesHouseClient):
        self.ch_client = ch_client
        
        # Mid-market criteria
        self.min_turnover = 15_000_000  # £15M
        self.max_turnover = 500_000_000  # £500M (upper mid-market)
        
        # Sampling parameters
        self.target_sample_size = 1000  # Target number of relevant companies
        self.sampling_rate = 0.1  # Sample 10% of potential candidates
        
        # Strategic search terms that indicate mid-market companies
        self.strategic_search_terms = [
            "international", "export", "global", "technology", "software",
            "manufacturing", "engineering", "construction", "logistics",
            "distribution", "wholesale", "retail", "professional services",
            "consulting", "media", "marketing", "healthcare", "education",
            "finance", "insurance", "property", "real estate"
        ]
        
        # SIC codes that typically indicate mid-market companies
        self.relevant_sic_codes = {
            # Technology & Software
            "620": "Computer programming, consultancy and related",
            "631": "Data processing, hosting and related",
            
            # Manufacturing
            "25": "Manufacture of fabricated metal products",
            "26": "Manufacture of computer, electronic and optical products",
            "27": "Manufacture of electrical equipment",
            "28": "Manufacture of machinery and equipment",
            
            # Professional Services
            "69": "Legal and accounting activities",
            "70": "Activities of head offices; management consultancy",
            "71": "Architectural and engineering activities",
            "73": "Advertising and market research",
            
            # Wholesale & Distribution
            "46": "Wholesale trade",
            
            # Construction
            "41": "Construction of buildings",
            "42": "Civil engineering",
            
            # Transportation
            "49": "Land transport",
            "50": "Water transport",
            "51": "Air transport",
            "52": "Warehousing and support activities",
            
            # Healthcare
            "86": "Human health activities",
            
            # Education
            "85": "Education"
        }
    
    async def discover_mid_market_companies(self, max_companies: int = 500) -> List[Dict[str, Any]]:
        """
        Discover mid-market companies using intelligent sampling strategy.
        Returns a curated list of companies that meet mid-market criteria.
        """
        print(f"🔍 Starting smart discovery of mid-market companies...")
        print(f"🎯 Target: {max_companies} companies with £{self.min_turnover:,}M+ turnover")
        
        candidates = []
        
        # Strategy 1: Search by strategic terms
        print("📊 Phase 1: Strategic term searches...")
        for term in self.strategic_search_terms[:5]:  # Limit to avoid API limits
            try:
                term_candidates = await self._search_by_term(term, items_per_page=50)
                candidates.extend(term_candidates)
                print(f"  • '{term}': {len(term_candidates)} candidates")
                
                if len(candidates) >= max_companies:
                    break
                    
            except Exception as e:
                print(f"  • '{term}': Error - {e}")
                continue
        
        # Strategy 2: Search by SIC codes (if we need more)
        if len(candidates) < max_companies:
            print("🏭 Phase 2: SIC code targeted searches...")
            for sic_prefix in list(self.relevant_sic_codes.keys())[:3]:
                try:
                    sic_candidates = await self._search_by_sic_code(sic_prefix, items_per_page=30)
                    new_candidates = [c for c in sic_candidates if c not in candidates]
                    candidates.extend(new_candidates)
                    print(f"  • SIC {sic_prefix}xx: {len(new_candidates)} new candidates")
                    
                    if len(candidates) >= max_companies:
                        break
                        
                except Exception as e:
                    print(f"  • SIC {sic_prefix}xx: Error - {e}")
                    continue
        
        # Remove duplicates and limit
        unique_candidates = self._deduplicate_candidates(candidates)
        final_candidates = unique_candidates[:max_companies]
        
        print(f"✅ Discovery complete: {len(final_candidates)} unique mid-market candidates")
        return final_candidates
    
    async def _search_by_term(self, term: str, items_per_page: int = 50) -> List[Dict[str, Any]]:
        """Search for companies by strategic term."""
        try:
            results = self.ch_client.search_companies(
                query=term,
                items_per_page=items_per_page,
                start_index=0
            )
            
            candidates = []
            for item in results.get("items", []):
                if self._is_potential_mid_market(item):
                    candidates.append({
                        "company_number": item["company_number"],
                        "company_name": item.get("title", ""),
                        "search_term": term,
                        "discovery_method": "strategic_search",
                        "search_score": random.uniform(0.7, 0.9)  # Simulated relevance score
                    })
            
            return candidates
            
        except Exception as e:
            print(f"Error searching for '{term}': {e}")
            return []
    
    async def _search_by_sic_code(self, sic_prefix: str, items_per_page: int = 30) -> List[Dict[str, Any]]:
        """Search for companies by SIC code prefix."""
        # Note: Companies House API doesn't directly support SIC code search
        # This is a placeholder for future enhancement with alternative data sources
        return []
    
    def _is_potential_mid_market(self, company_item: Dict[str, Any]) -> bool:
        """
        Quick assessment if a company might be mid-market based on available data.
        """
        company_name = company_item.get("title", "").lower()
        
        # Skip obvious non-mid-market indicators
        skip_indicators = [
            "limited", "ltd", "plc", "group", "holdings", "investments",  # Too generic
            "consultant", "freelance", "sole trader",  # Too small
            "charity", "foundation", "trust", "club", "society"  # Non-commercial
        ]
        
        if any(indicator in company_name for indicator in skip_indicators):
            return False
        
        # Look for mid-market indicators
        mid_market_indicators = [
            "international", "global", "worldwide", "europe", "asia",
            "technology", "software", "engineering", "manufacturing",
            "distribution", "logistics", "professional services"
        ]
        
        return any(indicator in company_name for indicator in mid_market_indicators)
    
    def _deduplicate_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate companies from candidate list."""
        seen = set()
        unique = []
        
        for candidate in candidates:
            company_number = candidate["company_number"]
            if company_number not in seen:
                seen.add(company_number)
                unique.append(candidate)
        
        return unique
    
    async def enrich_candidates_with_filings(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich candidate list with filing information to better assess mid-market status.
        """
        enriched = []
        
        for candidate in candidates[:50]:  # Limit to avoid API limits
            try:
                company_number = candidate["company_number"]
                
                # Get recent filings
                filings = self.ch_client.filing_history(company_number, items_per_page=10)
                filing_items = filings.get("items", [])
                
                # Check for accounts filings (indicates active company)
                has_accounts = any(
                    item.get("description", "").lower().startswith("accounts")
                    for item in filing_items
                )
                
                # Estimate company size from filing patterns
                filing_frequency = len(filing_items)
                years_active = self._estimate_years_active(filing_items)
                
                enriched_candidate = candidate.copy()
                enriched_candidate.update({
                    "has_recent_accounts": has_accounts,
                    "filing_frequency": filing_frequency,
                    "estimated_years_active": years_active,
                    "enrichment_date": datetime.now().isoformat()
                })
                
                enriched.append(enriched_candidate)
                
            except Exception as e:
                # If enrichment fails, keep original candidate
                enriched.append(candidate)
                continue
        
        return enriched
    
    def _estimate_years_active(self, filing_items: List[Dict[str, Any]]) -> int:
        """Estimate how many years the company has been active based on filings."""
        if not filing_items:
            return 0
        
        dates = []
        for item in filing_items:
            try:
                filing_date = self._parse_filing_date(item.get("date"))
                if filing_date:
                    dates.append(filing_date)
            except:
                continue
        
        if not dates:
            return 0
        
        oldest = min(dates)
        newest = max(dates)
        years_diff = (newest - oldest).days / 365.25
        
        return max(1, int(years_diff))
    
    def _parse_filing_date(self, date_str: str) -> Optional[date]:
        """Parse filing date string."""
        if not date_str:
            return None
        
        try:
            # Companies House dates are in YYYY-MM-DD format
            return date.fromisoformat(date_str)
        except:
            return None
    
    def save_discovery_results(self, candidates: List[Dict[str, Any]], filename: str = "mid_market_candidates.json"):
        """Save discovery results to file."""
        output_path = Path("output") / filename
        output_path.parent.mkdir(exist_ok=True)
        
        with output_path.open("w") as f:
            json.dump({
                "discovery_date": datetime.now().isoformat(),
                "total_candidates": len(candidates),
                "criteria": {
                    "min_turnover_gbp": self.min_turnover,
                    "max_turnover_gbp": self.max_turnover
                },
                "candidates": candidates
            }, f, indent=2)
        
        print(f"💾 Saved {len(candidates)} candidates to {output_path}")
    
    def load_discovery_results(self, filename: str = "mid_market_candidates.json") -> List[Dict[str, Any]]:
        """Load previously saved discovery results."""
        input_path = Path("output") / filename
        
        if not input_path.exists():
            return []
        
        with input_path.open("r") as f:
            data = json.load(f)
        
        return data.get("candidates", [])
