"""
Scenario Generation for Tax Information Retrieval Evaluation

Generates synthetic and semi-synthetic tax scenarios for testing
the retrieval, extraction, and reasoning components.
"""

import json
import random
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, date
import itertools


class TaxScenarioGenerator:
    """Generate tax scenarios with controlled variation"""
    
    def __init__(self, output_dir: str = "data/processed/scenarios"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Scenario templates and parameters
        self.jurisdictions = self._init_jurisdictions()
        self.tax_types = self._init_tax_types()
        self.taxpayer_profiles = self._init_taxpayer_profiles()
        self.scenarios = []
    
    def _init_jurisdictions(self) -> List[Dict]:
        """Initialize jurisdiction configurations"""
        return [
            {
                'level': 'federal',
                'name': 'United States',
                'code': 'US',
                'authority': 'IRS'
            },
            {
                'level': 'state',
                'name': 'California',
                'code': 'CA',
                'authority': 'California Franchise Tax Board'
            },
            {
                'level': 'state',
                'name': 'New York',
                'code': 'NY',
                'authority': 'New York Department of Taxation and Finance'
            },
            {
                'level': 'state',
                'name': 'Texas',
                'code': 'TX',
                'authority': 'Texas Comptroller of Public Accounts'
            },
            {
                'level': 'state',
                'name': 'Florida',
                'code': 'FL',
                'authority': 'Florida Department of Revenue'
            },
            {
                'level': 'local',
                'name': 'New York City',
                'code': 'NYC',
                'state': 'NY',
                'authority': 'NYC Department of Finance'
            },
            {
                'level': 'local',
                'name': 'San Francisco',
                'code': 'SF',
                'state': 'CA',
                'authority': 'San Francisco Tax Collector'
            }
        ]
    
    def _init_tax_types(self) -> List[Dict]:
        """Initialize tax type configurations"""
        return [
            {
                'type': 'income',
                'subtypes': ['individual', 'corporate', 'partnership', 'estate'],
                'common_provisions': ['standard_deduction', 'itemized_deductions', 'credits', 'brackets']
            },
            {
                'type': 'sales',
                'subtypes': ['general', 'use_tax', 'marketplace'],
                'common_provisions': ['rate', 'exemptions', 'nexus']
            },
            {
                'type': 'property',
                'subtypes': ['real_property', 'personal_property', 'business_property'],
                'common_provisions': ['assessment', 'exemptions', 'rates']
            },
            {
                'type': 'payroll',
                'subtypes': ['unemployment', 'disability', 'training'],
                'common_provisions': ['wage_base', 'rate', 'employer_requirements']
            },
            {
                'type': 'excise',
                'subtypes': ['fuel', 'tobacco', 'alcohol'],
                'common_provisions': ['rate', 'registration', 'reporting']
            }
        ]
    
    def _init_taxpayer_profiles(self) -> List[Dict]:
        """Initialize taxpayer profile templates"""
        return [
            {
                'type': 'individual',
                'filing_status': ['single', 'married_joint', 'married_separate', 'head_of_household'],
                'income_ranges': [(0, 25000), (25000, 75000), (75000, 150000), (150000, 500000), (500000, float('inf'))],
                'special_situations': [None, 'self_employed', 'rental_income', 'foreign_income', 'investment_income']
            },
            {
                'type': 'small_business',
                'entity_types': ['sole_proprietor', 'llc', 's_corp', 'partnership'],
                'revenue_ranges': [(0, 100000), (100000, 500000), (500000, 2000000), (2000000, float('inf'))],
                'employee_counts': [0, 1, 5, 10, 25, 50],
                'special_situations': [None, 'multi_state', 'online_sales', 'remote_employees']
            },
            {
                'type': 'corporation',
                'entity_types': ['c_corp', 's_corp'],
                'revenue_ranges': [(0, 1000000), (1000000, 10000000), (10000000, float('inf'))],
                'special_situations': [None, 'multi_state', 'international', 'publicly_traded']
            }
        ]
    
    def generate_income_tax_scenario(self, jurisdiction: Dict, year: int) -> Dict:
        """Generate individual income tax scenario"""
        
        profile = random.choice([p for p in self.taxpayer_profiles if p['type'] == 'individual'])
        filing_status = random.choice(profile['filing_status'])
        income_range = random.choice(profile['income_ranges'])
        income = random.randint(int(income_range[0]), min(int(income_range[1]), 1000000))
        
        scenario = {
            'scenario_id': f"scenario_{len(self.scenarios) + 1:04d}",
            'jurisdiction': jurisdiction['name'],
            'jurisdiction_code': jurisdiction['code'],
            'jurisdiction_level': jurisdiction['level'],
            'tax_type': 'income',
            'tax_subtype': 'individual',
            'tax_year': year,
            'taxpayer': {
                'type': 'individual',
                'filing_status': filing_status,
                'gross_income': income,
                'age': random.choice([25, 35, 45, 55, 65, 70]),
                'dependents': random.choice([0, 0, 1, 2, 3])
            },
            'query': self._generate_income_tax_query(filing_status, income, jurisdiction, year),
            'relevant_provisions': [],  # To be filled by annotator
            'expected_forms': [],  # To be filled by annotator
            'expected_deadlines': [],  # To be filled by annotator
            'complexity': 'simple',
            'tags': ['income_tax', filing_status, jurisdiction['code']],
            'created_date': datetime.now().isoformat()
        }
        
        # Add special situations
        special = random.choice(profile['special_situations'])
        if special:
            scenario['taxpayer']['special_situation'] = special
            scenario['tags'].append(special)
            scenario['complexity'] = 'moderate' if special != 'foreign_income' else 'complex'
        
        return scenario
    
    def _generate_income_tax_query(self, filing_status: str, income: int, jurisdiction: Dict, year: int) -> str:
        """Generate natural language query for income tax scenario"""
        
        status_text = {
            'single': 'single',
            'married_joint': 'married filing jointly',
            'married_separate': 'married filing separately',
            'head_of_household': 'filing as head of household'
        }
        
        queries = [
            f"A {status_text[filing_status]} taxpayer with ${income:,} gross income in {year}: what are the filing requirements in {jurisdiction['name']}?",
            f"What forms must be filed for {status_text[filing_status]} individual earning ${income:,} in {jurisdiction['name']} for tax year {year}?",
            f"Individual income tax obligations for {jurisdiction['name']} resident, {status_text[filing_status]}, ${income:,} income, {year}",
        ]
        
        return random.choice(queries)
    
    def generate_sales_tax_scenario(self, jurisdiction: Dict, year: int) -> Dict:
        """Generate sales tax scenario"""
        
        profile = random.choice([p for p in self.taxpayer_profiles if p['type'] == 'small_business'])
        revenue_range = random.choice(profile['revenue_ranges'])
        revenue = random.randint(int(revenue_range[0]), min(int(revenue_range[1]), 10000000))
        
        scenario = {
            'scenario_id': f"scenario_{len(self.scenarios) + 1:04d}",
            'jurisdiction': jurisdiction['name'],
            'jurisdiction_code': jurisdiction['code'],
            'jurisdiction_level': jurisdiction['level'],
            'tax_type': 'sales',
            'tax_subtype': random.choice(['general', 'use_tax', 'marketplace']),
            'tax_year': year,
            'taxpayer': {
                'type': 'business',
                'entity_type': random.choice(profile['entity_types']),
                'annual_revenue': revenue,
                'has_physical_presence': random.choice([True, False]),
                'has_economic_nexus': random.choice([True, False]),
                'sales_channels': random.choice([['retail'], ['online'], ['retail', 'online']])
            },
            'query': self._generate_sales_tax_query(revenue, jurisdiction, year),
            'relevant_provisions': [],
            'expected_forms': [],
            'expected_deadlines': [],
            'complexity': 'moderate',
            'tags': ['sales_tax', jurisdiction['code']],
            'created_date': datetime.now().isoformat()
        }
        
        if not scenario['taxpayer']['has_physical_presence'] and scenario['taxpayer']['has_economic_nexus']:
            scenario['complexity'] = 'complex'
            scenario['tags'].append('economic_nexus')
        
        return scenario
    
    def _generate_sales_tax_query(self, revenue: int, jurisdiction: Dict, year: int) -> str:
        """Generate sales tax query"""
        
        queries = [
            f"What are the sales tax collection and filing requirements for a business with ${revenue:,} annual revenue in {jurisdiction['name']} in {year}?",
            f"Sales tax nexus and obligations for online seller earning ${revenue:,} in {jurisdiction['name']}, tax year {year}",
            f"Does a business with ${revenue:,} revenue need to collect sales tax in {jurisdiction['name']}? What forms are required?",
        ]
        
        return random.choice(queries)
    
    def generate_multi_jurisdiction_scenario(self, jurisdictions: List[Dict], year: int) -> Dict:
        """Generate complex multi-jurisdiction scenario"""
        
        primary_jurisdiction = jurisdictions[0]
        
        scenario = {
            'scenario_id': f"scenario_{len(self.scenarios) + 1:04d}",
            'jurisdiction': 'Multiple',
            'jurisdictions': [j['code'] for j in jurisdictions],
            'primary_jurisdiction': primary_jurisdiction['code'],
            'tax_type': random.choice(['income', 'sales']),
            'tax_year': year,
            'taxpayer': {
                'type': 'business',
                'entity_type': 'llc',
                'primary_location': primary_jurisdiction['name'],
                'other_locations': [j['name'] for j in jurisdictions[1:]],
                'annual_revenue': random.randint(500000, 5000000)
            },
            'query': f"What are the tax filing obligations for a business operating in {', '.join(j['name'] for j in jurisdictions)} for tax year {year}?",
            'relevant_provisions': [],
            'expected_forms': [],
            'expected_deadlines': [],
            'complexity': 'complex',
            'tags': ['multi_jurisdiction'] + [j['code'] for j in jurisdictions],
            'created_date': datetime.now().isoformat()
        }
        
        return scenario
    
    def generate_scenario_set(
        self,
        n_scenarios: int = 100,
        tax_years: List[int] = None,
        complexity_distribution: Dict[str, float] = None
    ) -> List[Dict]:
        """
        Generate a balanced set of scenarios
        
        Args:
            n_scenarios: Total number of scenarios to generate
            tax_years: List of tax years to cover (default: 2020-2025)
            complexity_distribution: {'simple': 0.4, 'moderate': 0.4, 'complex': 0.2}
        """
        
        if tax_years is None:
            tax_years = [2020, 2021, 2022, 2023, 2024, 2025]
        
        if complexity_distribution is None:
            complexity_distribution = {'simple': 0.3, 'moderate': 0.5, 'complex': 0.2}
        
        scenarios = []
        
        # Calculate target counts
        targets = {
            'simple': int(n_scenarios * complexity_distribution['simple']),
            'moderate': int(n_scenarios * complexity_distribution['moderate']),
            'complex': int(n_scenarios * complexity_distribution['complex'])
        }
        
        counts = {'simple': 0, 'moderate': 0, 'complex': 0}
        
        for i in range(n_scenarios):
            year = random.choice(tax_years)
            jurisdiction = random.choice(self.jurisdictions)
            
            # Decide scenario type based on complexity targets
            if counts['simple'] < targets['simple']:
                scenario = self.generate_income_tax_scenario(jurisdiction, year)
            elif counts['moderate'] < targets['moderate']:
                scenario = self.generate_sales_tax_scenario(jurisdiction, year)
            else:
                # Generate multi-jurisdiction (complex)
                jurisdictions = random.sample(self.jurisdictions[:5], k=random.randint(2, 3))
                scenario = self.generate_multi_jurisdiction_scenario(jurisdictions, year)
            
            # Update complexity counts
            counts[scenario['complexity']] += 1
            scenarios.append(scenario)
        
        self.scenarios = scenarios
        return scenarios
    
    def save_scenarios(self, filename: str = "scenarios.jsonl"):
        """Save scenarios to JSONL file"""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for scenario in self.scenarios:
                f.write(json.dumps(scenario, ensure_ascii=False) + '\n')
        
        # Save summary
        summary = {
            'total_scenarios': len(self.scenarios),
            'by_complexity': {
                'simple': sum(1 for s in self.scenarios if s['complexity'] == 'simple'),
                'moderate': sum(1 for s in self.scenarios if s['complexity'] == 'moderate'),
                'complex': sum(1 for s in self.scenarios if s['complexity'] == 'complex')
            },
            'by_jurisdiction': {
                jur['code']: sum(1 for s in self.scenarios if s.get('jurisdiction_code') == jur['code'])
                for jur in self.jurisdictions
            },
            'by_tax_type': {
                'income': sum(1 for s in self.scenarios if s['tax_type'] == 'income'),
                'sales': sum(1 for s in self.scenarios if s['tax_type'] == 'sales'),
                'other': sum(1 for s in self.scenarios if s['tax_type'] not in ['income', 'sales'])
            },
            'generated_date': datetime.now().isoformat()
        }
        
        with open(self.output_dir / "scenario_summary.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"Saved {len(self.scenarios)} scenarios to {filepath}")
        print(f"Summary: {summary}")


def main():
    """Main execution"""
    print("=" * 60)
    print("Tax Scenario Generator")
    print("=" * 60)
    print()
    
    generator = TaxScenarioGenerator()
    
    print("Generate scenario set...")
    n_scenarios = int(input("Number of scenarios (default 100): ").strip() or "100")
    
    print("\nGenerating scenarios...")
    scenarios = generator.generate_scenario_set(n_scenarios=n_scenarios)
    
    print("\nSample scenarios:")
    for i, scenario in enumerate(scenarios[:3], 1):
        print(f"\n{i}. {scenario['scenario_id']}")
        print(f"   Query: {scenario['query']}")
        print(f"   Complexity: {scenario['complexity']}")
        print(f"   Jurisdiction: {scenario['jurisdiction']}")
    
    save = input("\nSave scenarios? (y/n): ").lower()
    if save == 'y':
        generator.save_scenarios()
        print("\nScenarios saved to data/processed/scenarios/")
    
    print("\nNext steps:")
    print("1. Review generated scenarios for realism")
    print("2. Add manual edge cases and special situations")
    print("3. Begin annotation using annotation tools")


if __name__ == "__main__":
    main()
