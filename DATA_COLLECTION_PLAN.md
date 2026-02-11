# Legal Tax IR System - Data Collection & Scraping Plan

## Overview
This plan outlines data collection for a multi-layered legal tax information retrieval system with evaluation across retrieval, extraction, and reasoning components.

---

## Phase 1: Legal Statute Collection (AUTOMATED)

### 1.1 Federal Tax Code (IRS)
**Source**: IRS.gov, Cornell LII
**Data Needed**:
- Internal Revenue Code sections (26 USC)
- IRS Publications and Forms
- Effective dates and amendments
- Cross-references

**Automation**: `scrapers/federal_tax_scraper.py`
**Manual**: Verify section numbering consistency

**IRC Section Coverage** (280+ sections):
The scraper includes comprehensive coverage across all major IRC subtitles:

- **Subtitle A - Income Taxes** (~230 sections):
  - Subchapter A: Tax determination (§1, 11, 55, 59)
  - Subchapter B: Gross income, deductions (§61-291) - includes income definitions, exclusions, business/personal deductions
  - Subchapter C: Corporate distributions (§301-385) - dividends, redemptions, reorganizations
  - Subchapter D: Deferred compensation (§401-436) - qualified plans, IRAs, stock options
  - Subchapter E: Accounting methods (§441-483) - timing, inventories, at-risk, passive activity
  - Subchapter F: Exempt organizations (§501-530) - tax-exempt entities, UBIT, political orgs
  - Subchapter J: Estates & trusts (§641-692) - trust taxation, grantor trusts
  - Subchapter K: Partnerships (§701-777) - pass-through taxation, allocations, basis
  - Subchapter N: International (§861-999) - source rules, foreign tax credit, CFC, PFIC, GILTI
  - Subchapter P: Capital gains (§1201-1298) - asset classification, holding periods, recapture
  - Subchapter S: S corporations (§1361-1379) - election, pass-through, built-in gains

- **Subtitle B - Estate & Gift Taxes** (~30 sections):
  - Chapter 11: Estate tax (§2001-2058) - rates, gross estate, deductions, marital deduction
  - Chapter 12: Gift tax (§2501-2523) - taxable gifts, annual exclusion, split gifts

- **Subtitle C - Employment Taxes** (~20 sections):
  - Chapter 21: FICA (§3101-3128) - social security/Medicare taxes
  - Chapter 23: FUTA (§3301-3311) - unemployment taxes
  - Chapter 24: Withholding (§3401-3406) - income tax withholding, backup withholding

- **Subtitle D - Excise Taxes** (selective ~20 sections):
  - Key excise taxes: fuel, trucks, tires, communications, air travel, wagering
  - Qualified plan penalties (§4971-4980H) - including ACA employer mandate

- **Tax Credits** (~30 sections):
  - Personal: child tax credit, EITC, education, adoption, saver's credit
  - Business: R&D, low-income housing, work opportunity, renewable energy
  - Energy: residential/commercial efficiency, electric vehicles

**Scraping Strategy**:
1. Primary: Chapter-based discovery (attempts to parse Cornell LII structure)
2. Fallback 1: Direct section discovery (if HTML structure changed)
3. Fallback 2: Predefined important sections list (280+ sections, guaranteed coverage)

**Time Estimate**: ~5 minutes for 280 sections @ 1 second rate limit
**Coverage**: 99%+ of real-world tax scenarios for production systems

### 1.2 State Tax Codes
**Sources**: State revenue department websites (50 states + DC)
**Data Needed**:
- Income tax statutes
- Sales/use tax codes
- Property tax codes
- Filing requirements
- Effective dates by tax year

**Automation**: `scrapers/state_tax_scraper.py`
**Manual**: 
- Identify each state's statute URL pattern
- Handle states with non-standard formats (PDF-only, protected sites)
- Verify jurisdiction metadata

### 1.3 Local Tax Ordinances
**Sources**: City/county websites
**Data Needed**:
- Municipal tax codes
- Local filing requirements
- Special district taxes

**Automation**: Limited - many require manual download
**Manual**: 
- Select representative jurisdictions (5-10 major cities)
- Download PDF ordinances manually
- Extract text using OCR if needed

---

## Phase 2: Benchmark Dataset Collection (SEMI-AUTOMATED)

### 2.1 COLIEE Dataset
**Source**: COLIEE competition website
**Data Needed**:
- Legal case retrieval tasks
- Statute law retrieval tasks
- Gold annotations

**Action**: Download from official source (requires registration)
**Manual**: Register and download dataset

### 2.2 TREC Legal Track (if available)
**Source**: TREC archives
**Manual**: Check availability and licensing

---

## Phase 3: Scenario Generation (AUTOMATED + MANUAL)

### 3.1 Real-World Scenarios
**Sources**: 
- Tax court cases (Tax Court website)
- IRS rulings and letter rulings
- State revenue department guidance
- Tax professional forums (r/taxpros, discussions)

**Automation**: `scrapers/case_scraper.py` for Tax Court cases
**Manual**: 
- Curate 100-200 representative scenarios
- Cover diverse tax types (income, sales, property, payroll)
- Include edge cases and multi-jurisdiction scenarios

### 3.2 Synthetic Scenarios
**Generation**: Use templates + parameter variation
**Automation**: `scenarios/scenario_generator.py`
**Parameters to vary**:
- Jurisdiction (federal, state, local)
- Tax type
- Taxpayer type (individual, business, non-profit)
- Income/revenue ranges
- Time periods (2020-2025)
- Special conditions (multiple states, foreign income, etc.)

**Manual**: Review generated scenarios for realism

---

## Phase 4: Gold Standard Annotation (MANUAL-INTENSIVE)

### 4.1 Retrieval Gold Labels
For each scenario, annotate:
- **All relevant statute sections** (for recall measurement)
- **Most controlling section** (for MRR)
- **Relevance grades** (1-3 scale for nDCG)
- **Mandatory sections** (cannot miss)

**Tool**: `annotation/retrieval_annotator.py` (GUI for faster labeling)
**Manual**: Law student or tax professional review (100-200 hours estimated)

### 4.2 Extraction Gold Labels
For each relevant section, annotate:
- **Condition spans** (eligibility criteria)
- **Exception spans**
- **Definition spans**
- **Numeric values** (thresholds, rates, amounts)
- **Dates** (effective dates, deadlines)
- **Units** (annual/monthly, individual/joint)
- **Evidence spans** (which text supports each extraction)

**Tool**: `annotation/extraction_annotator.py`
**Manual**: Detailed legal annotation (200-400 hours estimated)

### 4.3 Reasoning Gold Labels
For each scenario, annotate:
- **Applicable jurisdictions and tax types**
- **Required forms**
- **Filing deadlines**
- **Expected outcomes** (tax owed, exemptions applied)
- **Explanation chains** (which rules lead to which conclusions)

**Tool**: `annotation/reasoning_annotator.py`
**Manual**: Expert tax professional review (150-300 hours estimated)

---

## Phase 5: Metadata Collection (AUTOMATED)

### 5.1 Jurisdiction Hierarchies
**Data Needed**:
- Federal > State > County > City relationships
- Precedence rules
- Effective date ranges

**Automation**: `utils/jurisdiction_mapper.py`
**Manual**: Verify precedence rules

### 5.2 Geocoding Data
**Data Needed**:
- ZIP codes to jurisdiction mapping
- County/city boundaries
- Special tax districts

**Source**: Census Bureau, USPS
**Automation**: `utils/geocoder.py`

### 5.3 Historical Tax Rates
**Data Needed**:
- Federal tax brackets by year (2018-2025)
- State tax rates by year
- Special rates (capital gains, corporate, etc.)

**Automation**: `scrapers/rates_scraper.py`
**Manual**: Verify against official publications

---

## Phase 6: Table and Form Extraction (SEMI-AUTOMATED)

### 6.1 Tax Forms
**Source**: IRS forms, state forms
**Data Needed**:
- Form fields and line items
- Instructions
- Schedules and dependencies

**Automation**: `scrapers/forms_scraper.py` + `utils/pdf_table_extractor.py`
**Manual**: Verify complex table structures

### 6.2 Tax Tables
**Examples**: Tax bracket tables, standard deduction tables, AMT tables
**Automation**: Camelot or Tabula for PDF table extraction
**Manual**: Verify accuracy, especially for multi-part tables

---

## Implementation Priority

### HIGH PRIORITY (Start Immediately)
1. Federal tax code scraping (26 USC) - **automated**
2. Scenario generation from templates - **automated**
3. Select 3-5 states for initial dataset - **manual selection**
4. Basic retrieval annotation tool - **semi-automated**

### MEDIUM PRIORITY (Week 2-3)
5. State tax code scraping for selected states - **automated**
6. COLIEE dataset download - **manual**
7. Extraction annotation tool - **semi-automated**
8. Tax Court case scraping - **automated**

### LOWER PRIORITY (Week 4+)
9. Remaining states
10. Local ordinances (manual)
11. Historical rate collection
12. Form extraction and parsing

---

## Data Storage Structure

```
data/
├── raw/
│   ├── federal/
│   │   ├── usc_title26/          # Raw statute text
│   │   ├── irs_publications/
│   │   └── forms/
│   ├── states/
│   │   ├── california/
│   │   ├── new_york/
│   │   └── ...
│   └── benchmark/
│       ├── coliee/
│       └── trec/
├── processed/
│   ├── statutes/                 # Cleaned, sectioned text
│   ├── scenarios/                # Test scenarios
│   └── tables/                   # Extracted structured data
├── annotations/
│   ├── retrieval_gold.jsonl      # Gold retrieval labels
│   ├── extraction_gold.jsonl     # Gold extraction labels
│   └── reasoning_gold.jsonl      # Gold reasoning labels
└── metadata/
    ├── jurisdictions.json
    ├── geocoding.json
    └── historical_rates.json
```

---

## Estimated Timeline

- **Week 1-2**: Federal + 3 states, basic scenarios (automated)
- **Week 3-4**: Annotation tools, initial gold labeling (manual-intensive)
- **Week 5-6**: Expand to 10 states, more scenarios
- **Week 7-8**: Benchmark integration, full annotation
- **Week 9+**: Refinement, edge cases, validation

---

## Quality Control

1. **Inter-annotator agreement**: 20% double-annotation for gold labels
2. **Expert review**: Tax professional reviews 10% sample
3. **Automated validation**: Schema checks, consistency tests
4. **Pilot study**: Test on 20 scenarios before full annotation

---

## Budget Estimates

- **Automation development**: 40-60 hours (your time)
- **Manual annotation**: 450-900 hours (can use law students at $25-40/hr)
- **Expert review**: 20-40 hours (tax professional at $100-200/hr)
- **Total cost (if outsourced)**: $13,000 - $44,000
