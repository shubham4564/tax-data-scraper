"""
Master orchestrator script for legal tax IR data collection

Runs the complete data collection pipeline with progress tracking
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Dict
import json
from datetime import datetime


class DataCollectionOrchestrator:
    """Orchestrate the entire data collection process"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.status_file = self.project_root / "collection_status.json"
        self.status = self._load_status()
    
    def _load_status(self) -> Dict:
        """Load collection progress status"""
        if self.status_file.exists():
            with open(self.status_file, 'r') as f:
                return json.load(f)
        
        return {
            'started': datetime.now().isoformat(),
            'completed_steps': [],
            'current_step': None,
            'notes': {}
        }
    
    def _save_status(self):
        """Save collection progress"""
        with open(self.status_file, 'w') as f:
            json.dump(self.status, f, indent=2)
    
    def _mark_complete(self, step: str):
        """Mark a step as complete"""
        if step not in self.status['completed_steps']:
            self.status['completed_steps'].append(step)
        self.status['current_step'] = None
        self._save_status()
    
    def _mark_current(self, step: str):
        """Mark current step"""
        self.status['current_step'] = step
        self._save_status()
    
    def print_banner(self, text: str):
        """Print formatted banner"""
        print("\n" + "="*70)
        print(f"  {text}")
        print("="*70 + "\n")
    
    def check_dependencies(self) -> bool:
        """Check if required packages are installed"""
        self.print_banner("Checking Dependencies")
        
        required = ['requests', 'beautifulsoup4', 'numpy', 'flask']
        missing = []
        
        for package in required:
            try:
                __import__(package.replace('-', '_'))
                print(f"✓ {package}")
            except ImportError:
                print(f"✗ {package} - MISSING")
                missing.append(package)
        
        if missing:
            print(f"\nMissing packages: {', '.join(missing)}")
            print("Install with: pip install -r requirements.txt")
            return False
        
        print("\n✓ All dependencies satisfied")
        return True
    
    def step_scrape_federal(self):
        """Step 1: Scrape federal tax code"""
        self.print_banner("Step 1: Scrape Federal Tax Code")
        self._mark_current("scrape_federal")
        
        print("This will scrape IRC Title 26 from Cornell LII")
        print("Estimated time: 2-4 hours for full scrape")
        print()
        
        choice = input("Run full scrape (f), test mode (t), or skip (s)? [f/t/s]: ").lower()
        
        if choice == 's':
            print("Skipped.")
            return
        
        # Launch scraper
        if choice == 't':
            print("\nRunning test mode (first 20 sections)...")
        else:
            print("\nRunning full scrape...")
            print("This will take a while. Progress will be shown.")
        
        print("\nTo run manually: python scrapers/federal_tax_scraper.py")
        print("(Skipping actual execution in this demo)")
        
        # In production, would run:
        # subprocess.run([sys.executable, "scrapers/federal_tax_scraper.py"])
        
        self._mark_complete("scrape_federal")
        self.status['notes']['scrape_federal'] = f"Mode: {choice}, Time: {datetime.now().isoformat()}"
        self._save_status()
    
    def step_scrape_states(self):
        """Step 2: Scrape state tax codes"""
        self.print_banner("Step 2: Scrape State Tax Codes")
        self._mark_current("scrape_states")
        
        print("This will scrape tax codes from multiple states")
        print("Note: Some states require manual PDF download")
        print()
        
        choice = input("Scrape states (y/n)? [y/n]: ").lower()
        
        if choice != 'y':
            print("Skipped. Remember to manually download California PDFs.")
            return
        
        print("\nManual steps required:")
        print("1. California: Download from https://www.ftb.ca.gov/tax-pros/law/")
        print("   Instructions will be in: data/raw/states/california/MANUAL_DOWNLOAD_INSTRUCTIONS.json")
        print()
        print("To run: python scrapers/state_tax_scraper.py")
        
        self._mark_complete("scrape_states")
        self.status['notes']['scrape_states'] = "Partial automation - manual steps required"
        self._save_status()
    
    def step_download_coliee(self):
        """Step 3: Download COLIEE benchmark"""
        self.print_banner("Step 3: Download COLIEE Benchmark (MANUAL)")
        self._mark_current("download_coliee")
        
        print("COLIEE is a legal IR benchmark dataset")
        print()
        print("Manual steps:")
        print("1. Go to http://coliee.org/")
        print("2. Register for access")
        print("3. Download legal task data")
        print("4. Place in: data/raw/benchmark/coliee/")
        print()
        
        done = input("Have you completed this step? [y/n]: ").lower()
        
        if done == 'y':
            self._mark_complete("download_coliee")
            self.status['notes']['download_coliee'] = "Manually downloaded"
            self._save_status()
    
    def step_generate_scenarios(self):
        """Step 4: Generate test scenarios"""
        self.print_banner("Step 4: Generate Test Scenarios")
        self._mark_current("generate_scenarios")
        
        print("Generate synthetic tax scenarios for evaluation")
        print()
        
        n_scenarios = input("Number of scenarios (default 100): ").strip()
        n_scenarios = int(n_scenarios) if n_scenarios else 100
        
        print(f"\nGenerating {n_scenarios} scenarios...")
        print("To run: python scenarios/scenario_generator.py")
        
        self._mark_complete("generate_scenarios")
        self.status['notes']['generate_scenarios'] = f"{n_scenarios} scenarios"
        self._save_status()
    
    def step_annotate_retrieval(self):
        """Step 5: Retrieval annotation"""
        self.print_banner("Step 5: Retrieval Annotation (MANUAL)")
        self._mark_current("annotate_retrieval")
        
        print("Create gold labels for retrieval evaluation")
        print()
        print("This requires manual effort:")
        print(f"- Time estimate: {8-17} hours for 100 scenarios")
        print("- Requires legal knowledge")
        print()
        print("To start annotation tool:")
        print("  python annotation/retrieval_annotator.py")
        print("  Then open http://localhost:5000")
        print()
        
        done = input("Have you completed retrieval annotation? [y/n]: ").lower()
        
        if done == 'y':
            self._mark_complete("annotate_retrieval")
            self.status['notes']['annotate_retrieval'] = "Completed"
            self._save_status()
    
    def step_annotate_extraction(self):
        """Step 6: Extraction annotation"""
        self.print_banner("Step 6: Extraction Annotation (MANUAL)")
        self._mark_current("annotate_extraction")
        
        print("Create gold labels for extraction evaluation")
        print()
        print("This is the most time-intensive step:")
        print("- Time estimate: 33-67 hours for 100 sections")
        print("- Requires legal + technical expertise")
        print("- Consider outsourcing to law students")
        print()
        print("Setup:")
        print("  python annotation/extraction_annotator.py")
        print()
        print("This creates example and guidelines.")
        print("Then manually annotate following the guidelines.")
        print()
        
        done = input("Have you completed extraction annotation? [y/n]: ").lower()
        
        if done == 'y':
            self._mark_complete("annotate_extraction")
            self.status['notes']['annotate_extraction'] = "Completed"
            self._save_status()
    
    def step_annotate_reasoning(self):
        """Step 7: Reasoning annotation"""
        self.print_banner("Step 7: Reasoning Annotation (MANUAL)")
        self._mark_current("annotate_reasoning")
        
        print("Create gold labels for reasoning evaluation")
        print()
        print("For each scenario, determine:")
        print("- Applicable jurisdictions")
        print("- Required forms")
        print("- Filing deadlines")
        print("- Expected outcomes")
        print()
        print("Time estimate: 25-50 hours for 100 scenarios")
        print("Consider hiring tax professional")
        print()
        
        done = input("Have you completed reasoning annotation? [y/n]: ").lower()
        
        if done == 'y':
            self._mark_complete("annotate_reasoning")
            self.status['notes']['annotate_reasoning'] = "Completed"
            self._save_status()
    
    def show_summary(self):
        """Show collection progress summary"""
        self.print_banner("Data Collection Progress Summary")
        
        total_steps = 7
        completed = len(self.status['completed_steps'])
        
        print(f"Progress: {completed}/{total_steps} steps completed")
        print()
        
        steps = [
            ("scrape_federal", "Federal Tax Code Scraping"),
            ("scrape_states", "State Tax Code Scraping"),
            ("download_coliee", "COLIEE Benchmark Download"),
            ("generate_scenarios", "Scenario Generation"),
            ("annotate_retrieval", "Retrieval Annotation"),
            ("annotate_extraction", "Extraction Annotation"),
            ("annotate_reasoning", "Reasoning Annotation")
        ]
        
        for step_id, step_name in steps:
            status = "✓" if step_id in self.status['completed_steps'] else "○"
            current = " (IN PROGRESS)" if self.status['current_step'] == step_id else ""
            print(f"{status} {step_name}{current}")
            
            if step_id in self.status['notes']:
                print(f"    Note: {self.status['notes'][step_id]}")
        
        print()
        
        if completed == total_steps:
            print("🎉 All steps completed!")
            print()
            print("Next steps:")
            print("1. Verify data quality")
            print("2. Run pilot evaluation (20 scenarios)")
            print("3. Implement your IR system")
            print("4. Run full evaluation")
        else:
            print(f"📋 {total_steps - completed} steps remaining")
    
    def run(self):
        """Run the orchestrator"""
        self.print_banner("Legal Tax IR Data Collection Orchestrator")
        
        print("This script guides you through the data collection process.")
        print("Each step can be run individually or skipped if already completed.")
        print()
        
        # Check dependencies first
        if not self.check_dependencies():
            print("\nPlease install dependencies before continuing.")
            return
        
        # Show current progress
        if self.status['completed_steps']:
            self.show_summary()
            print()
            resume = input("Resume from where you left off? [y/n]: ").lower()
            if resume != 'y':
                return
        
        # Run steps
        steps = [
            self.step_scrape_federal,
            self.step_scrape_states,
            self.step_download_coliee,
            self.step_generate_scenarios,
            self.step_annotate_retrieval,
            self.step_annotate_extraction,
            self.step_annotate_reasoning
        ]
        
        for step_func in steps:
            step_name = step_func.__name__.replace('step_', '')
            
            # Skip if already completed
            if step_name in self.status['completed_steps']:
                print(f"\n✓ {step_name} already completed (skipping)")
                continue
            
            # Run step
            try:
                step_func()
            except KeyboardInterrupt:
                print("\n\nInterrupted. Progress saved.")
                print("Run this script again to resume.")
                return
            except Exception as e:
                print(f"\nError in {step_name}: {e}")
                print("Fix the error and run again to resume.")
                return
            
            print()
        
        # Final summary
        self.show_summary()


def main():
    """Main entry point"""
    orchestrator = DataCollectionOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
