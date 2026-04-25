"""
Continuous monitoring system for tracking company changes and new prospects.
Monitors filing updates and maintains a live prospect database.
"""

import asyncio
import json
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
import hashlib

from src.clients.companies_house import CompaniesHouseClient
from src.services.prospect_pipeline import ProspectAnalysisPipeline

class ContinuousMonitor:
    """
    System for continuously monitoring companies and updating prospect intelligence.
    Tracks filing changes, new companies, and updates prospect scores over time.
    """
    
    def __init__(self, ch_client: CompaniesHouseClient, pipeline: ProspectAnalysisPipeline):
        self.ch_client = ch_client
        self.pipeline = pipeline
        
        # Monitoring configuration
        self.monitoring_window_days = 90  # Check last 90 days for updates
        self.batch_size = 50  # Process companies in batches
        self.update_interval_hours = 24  # Check for updates daily
        
        # Data persistence
        self.prospect_db_path = Path("output/prospect_database.json")
        self.monitoring_log_path = Path("output/monitoring_log.jsonl")
        
        # Initialize database if it doesn't exist
        self._init_database()
    
    def _init_database(self):
        """Initialize the prospect database structure."""
        if not self.prospect_db_path.exists():
            initial_db = {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_prospects": 0,
                "prospects": {},
                "monitoring_stats": {
                    "companies_added": 0,
                    "companies_updated": 0,
                    "filings_processed": 0,
                    "last_check_date": None
                }
            }
            
            self.prospect_db_path.parent.mkdir(exist_ok=True)
            with self.prospect_db_path.open("w") as f:
                json.dump(initial_db, f, indent=2)
    
    async def monitor_prospects(self, prospect_list: List[str]) -> Dict[str, Any]:
        """
        Monitor a list of prospect companies for updates and changes.
        Returns summary of changes detected.
        """
        print(f"🔄 Starting continuous monitoring of {len(prospect_list)} prospects...")
        
        # Load existing database
        db = self._load_database()
        changes_detected = {
            "new_filings": 0,
            "updated_companies": 0,
            "new_prospects": 0,
            "errors": 0
        }
        
        # Process in batches to avoid API limits
        for i in range(0, len(prospect_list), self.batch_size):
            batch = prospect_list[i:i + self.batch_size]
            print(f"📊 Processing batch {i//self.batch_size + 1}/{(len(prospect_list) + self.batch_size - 1)//self.batch_size}")
            
            batch_changes = await self._process_batch(batch, db)
            
            # Update change counters
            for key in changes_detected:
                changes_detected[key] += batch_changes.get(key, 0)
            
            # Save progress
            self._save_database(db)
            
            # Rate limiting
            await asyncio.sleep(1)
        
        # Final save
        db["last_updated"] = datetime.now().isoformat()
        db["monitoring_stats"]["last_check_date"] = datetime.now().isoformat()
        self._save_database(db)
        
        print("✅ Monitoring complete!")
        print(f"📈 Changes detected: {changes_detected}")
        
        return changes_detected
    
    async def _process_batch(self, company_numbers: List[str], db: Dict[str, Any]) -> Dict[str, Any]:
        """Process a batch of companies for monitoring."""
        batch_changes = {"new_filings": 0, "updated_companies": 0, "new_prospects": 0, "errors": 0}
        
        for company_number in company_numbers:
            try:
                changes = await self._check_company_updates(company_number, db)
                
                for key in batch_changes:
                    batch_changes[key] += changes.get(key, 0)
                    
            except Exception as e:
                print(f"❌ Error processing {company_number}: {e}")
                batch_changes["errors"] += 1
                self._log_error(company_number, str(e))
        
        return batch_changes
    
    async def _check_company_updates(self, company_number: str, db: Dict[str, Any]) -> Dict[str, Any]:
        """Check for updates to a specific company."""
        changes = {"new_filings": 0, "updated_companies": 0, "new_prospects": 0, "errors": 0}
        
        # Get recent filings
        cutoff_date = date.today() - timedelta(days=self.monitoring_window_days)
        
        try:
            filings_response = self.ch_client.filing_history(
                company_number, 
                items_per_page=20,  # Check recent filings
                start_index=0
            )
            
            filing_items = filings_response.get("items", [])
            
            # Filter to recent filings
            recent_filings = []
            for item in filing_items:
                filing_date = self._parse_filing_date(item.get("date"))
                if filing_date and filing_date >= cutoff_date:
                    recent_filings.append(item)
            
            # Check if we have this company in our database
            if company_number not in db["prospects"]:
                # New prospect - analyze fully
                print(f"🆕 New prospect detected: {company_number}")
                await self._analyze_new_prospect(company_number, recent_filings, db)
                changes["new_prospects"] += 1
                return changes
            
            # Existing prospect - check for new filings
            existing_data = db["prospects"][company_number]
            existing_filing_ids = set(existing_data.get("processed_filings", []))
            
            new_filings = []
            for filing in recent_filings:
                filing_id = filing.get("transaction_id") or filing.get("barcode")
                if filing_id and filing_id not in existing_filing_ids:
                    new_filings.append(filing)
            
            if new_filings:
                print(f"📄 {len(new_filings)} new filings for {company_number}")
                await self._update_prospect_with_filings(company_number, new_filings, db)
                changes["new_filings"] += len(new_filings)
                changes["updated_companies"] += 1
            
        except Exception as e:
            changes["errors"] += 1
            self._log_error(company_number, f"API error: {e}")
        
        return changes
    
    async def _analyze_new_prospect(self, company_number: str, recent_filings: List[Dict], db: Dict[str, Any]):
        """Analyze a newly discovered prospect."""
        try:
            # Run full analysis
            report = await self.pipeline.analyze_company(company_number)
            
            # Store in database
            db["prospects"][company_number] = {
                "company_name": report.company_overview.company_name,
                "added_date": datetime.now().isoformat(),
                "last_analyzed": datetime.now().isoformat(),
                "prospect_report": report.model_dump(),
                "processed_filings": [f.get("transaction_id") or f.get("barcode") for f in recent_filings],
                "monitoring_status": "active"
            }
            
            db["total_prospects"] += 1
            db["monitoring_stats"]["companies_added"] += 1
            
        except Exception as e:
            print(f"❌ Failed to analyze new prospect {company_number}: {e}")
    
    async def _update_prospect_with_filings(self, company_number: str, new_filings: List[Dict], db: Dict[str, Any]):
        """Update existing prospect with new filing information."""
        try:
            # Re-run analysis with new data
            report = await self.pipeline.analyze_company(company_number)
            
            # Update database
            prospect_data = db["prospects"][company_number]
            prospect_data["last_analyzed"] = datetime.now().isoformat()
            prospect_data["prospect_report"] = report.model_dump()
            
            # Add new filing IDs
            existing_ids = set(prospect_data.get("processed_filings", []))
            new_ids = [f.get("transaction_id") or f.get("barcode") for f in new_filings]
            prospect_data["processed_filings"] = list(existing_ids.union(new_ids))
            
            db["monitoring_stats"]["companies_updated"] += 1
            db["monitoring_stats"]["filings_processed"] += len(new_filings)
            
        except Exception as e:
            print(f"❌ Failed to update prospect {company_number}: {e}")
    
    def _parse_filing_date(self, date_str: str) -> Optional[date]:
        """Parse filing date string."""
        if not date_str:
            return None
        try:
            return date.fromisoformat(date_str)
        except:
            return None
    
    def _load_database(self) -> Dict[str, Any]:
        """Load the prospect database."""
        try:
            with self.prospect_db_path.open("r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading database: {e}")
            return self._create_empty_db()
    
    def _save_database(self, db: Dict[str, Any]):
        """Save the prospect database."""
        try:
            with self.prospect_db_path.open("w") as f:
                json.dump(db, f, indent=2)
        except Exception as e:
            print(f"Error saving database: {e}")
    
    def _create_empty_db(self) -> Dict[str, Any]:
        """Create empty database structure."""
        return {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "total_prospects": 0,
            "prospects": {},
            "monitoring_stats": {
                "companies_added": 0,
                "companies_updated": 0,
                "filings_processed": 0,
                "last_check_date": None
            }
        }
    
    def _log_error(self, company_number: str, error: str):
        """Log monitoring errors."""
        try:
            self.monitoring_log_path.parent.mkdir(exist_ok=True)
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "company_number": company_number,
                "error": error,
                "action": "monitoring_check"
            }
            
            with self.monitoring_log_path.open("a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            print(f"Failed to log error: {e}")
    
    def get_prospect_summary(self) -> Dict[str, Any]:
        """Get summary of current prospect database."""
        db = self._load_database()
        
        # Calculate some useful stats
        prospects = db.get("prospects", {})
        tier_counts = {"tier_1": 0, "tier_2": 0, "tier_3": 0}
        use_case_scores = {}
        
        for company_data in prospects.values():
            report = company_data.get("prospect_report", {})
            
            # Count tiers
            tier = report.get("priority_tier", "tier_3")
            tier_counts[tier] += 1
            
            # Aggregate use case scores
            for use_case, score in report.get("all_use_case_scores", {}).items():
                if use_case not in use_case_scores:
                    use_case_scores[use_case] = []
                use_case_scores[use_case].append(score)
        
        # Calculate averages
        avg_use_case_scores = {}
        for use_case, scores in use_case_scores.items():
            avg_use_case_scores[use_case] = sum(scores) / len(scores) if scores else 0
        
        return {
            "total_prospects": db.get("total_prospects", 0),
            "tier_breakdown": tier_counts,
            "average_use_case_scores": avg_use_case_scores,
            "last_updated": db.get("last_updated"),
            "monitoring_stats": db.get("monitoring_stats", {})
        }
    
    def get_priority_prospects(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get highest priority prospects for outreach."""
        db = self._load_database()
        prospects = []
        
        for company_number, data in db.get("prospects", {}).items():
            report = data.get("prospect_report", {})
            overall_score = report.get("overall_readiness_score", 0)
            
            prospects.append({
                "company_number": company_number,
                "company_name": data.get("company_name", "Unknown"),
                "overall_score": overall_score,
                "priority_tier": report.get("priority_tier", "tier_3"),
                "recommended_outreach": report.get("recommended_outreach_angle", ""),
                "last_analyzed": data.get("last_analyzed", "")
            })
        
        # Sort by score descending
        prospects.sort(key=lambda x: x["overall_score"], reverse=True)
        
        return prospects[:limit]
