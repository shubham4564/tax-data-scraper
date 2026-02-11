# Legal Tax IR System - Data Collection & Evaluation

## Overview

Complete framework for collecting data and evaluating a legal tax information retrieval system across three layers: **Retrieval → Extraction → Reasoning**.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     DATA COLLECTION PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐         │
│  │   SCRAPERS   │ => │  SCENARIOS   │ => │ ANNOTATIONS  │         │
│  │  (Automated) │    │ (Automated)  │    │   (Manual)   │         │
│  └──────────────┘    └──────────────┘    └──────────────┘         │
│         │                    │                    │                 │
│         ↓                    ↓                    ↓                 │
│  Federal + State       100-500 Test        Gold Standard           │
│  Tax Codes            Scenarios           Labels (R/E/R)           │
│                                                                      │
├─────────────────────────────────────────────────────────────────────┤
│                     EVALUATION METRICS                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  RETRIEVAL:          EXTRACTION:          REASONING:                │
│  • Recall@k          • Span F1            • Applicability Acc       │
│  • nDCG@k            • Numeric Acc        • Form F1                 │
│  • MRR               • Date Correct       • Brier Score             │
│  • No-Miss Rate      • Attribution        • Calibration (ECE)       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)**: 5-minute quick start guide
- **[DATA_COLLECTION_PLAN.md](DATA_COLLECTION_PLAN.md)**: Complete data collection strategy and timeline
- **[IRC_SECTION_COVERAGE.md](IRC_SECTION_COVERAGE.md)**: Comprehensive documentation of 280+ IRC sections
- **[STATE_TAX_CODES.md](STATE_TAX_CODES.md)**: All 50 states + DC tax code URLs and scraping guide
- **[MANUAL_STEPS.md](MANUAL_STEPS.md)**: Manual intervention reference with time/cost estimates
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)**: Technical architecture and design decisions

## Quick Start Guide

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Optional: For PDF table extraction
pip install 'camelot-py[cv]'
```

### Execution Workflow

## Phase 1: Data Collection (Automated + Manual)

### Step 1.1: Scrape Federal Tax Code
```bash
# Full scrape (takes ~2-4 hours)
python scrapers/federal_tax_scraper.py

# Test mode (first 20 sections)
python scrapers/federal_tax_scraper.py
# Choose option 2 when prompted
```

**Output**: `data/raw/federal/usc_title26/`

**Manual intervention**:
- If CAPTCHA appears, solve it manually
- Verify section numbering is consistent

#### IRC Section Coverage

The federal scraper includes **280+ IRC sections** providing comprehensive coverage:

**Scraping Options**:
1. **Full chapter-based scrape**: Attempts to discover all IRC chapters and sections
2. **Test mode**: First 20 sections for quick validation
3. **Important sections mode** (recommended): 280+ predefined sections covering all major tax areas
4. **IRS Publications**: Download key publications (Pub 17, 334, 463, 501, 502, etc.) for 2020-2025

**Section Coverage Breakdown**:

| IRC Subtitle | Sections | Coverage |
|--------------|----------|----------|
| **Subtitle A: Income Taxes** | ~230 | Individual rates, corporate tax, deductions, credits, accounting methods, partnerships, S-corps, international, capital gains |
| **Subtitle B: Estate & Gift** | ~30 | Estate tax (§2001-2058), gift tax (§2501-2523), valuation rules |
| **Subtitle C: Employment** | ~20 | FICA (§3101+), FUTA (§3301+), withholding (§3401+) |
| **Subtitle D: Excise Taxes** | ~20 | Selective excise taxes, qualified plan penalties, ACA employer mandate |
| **Credits** | ~30 | Child tax credit, EITC, education, adoption, business, energy credits |

**Key Functional Areas Included**:
- ✅ Individual income tax (rates, income, deductions, credits)
- ✅ Corporate taxation (distributions, reorganizations, consolidated returns)
- ✅ Partnerships (allocations, basis, distributions, hot assets)
- ✅ S corporations (election, pass-through, built-in gains)
- ✅ Retirement & compensation (401(k), IRAs, stock options, deferred comp)
- ✅ International tax (foreign tax credit, CFC/Subpart F, PFIC, GILTI)
- ✅ Capital gains & losses (basis rules, like-kind exchanges, recapture)
- ✅ Trusts & estates (grantor trusts, complex trusts, estate income)
- ✅ Tax-exempt organizations (501(c)(3), UBIT, political orgs)
- ✅ Accounting methods (cash vs accrual, installment sales, mark-to-market)
- ✅ Estate & gift tax (unified credit, marital deduction, generation-skipping)
- ✅ Employment taxes (FICA, FUTA, withholding, backup withholding)

**Recommendation by Use Case**:
- **Academic pilot/proof-of-concept**: Use option 3 with `max_sections=50` (first 50 sections, ~1 minute)
- **Research paper/benchmark**: Use option 3 full mode (280 sections, ~5 minutes)  
- **Production legal system**: Use option 1 or 3 full mode for complete coverage

### Step 1.2: Scrape State Tax Codes
```bash
python scrapers/state_tax_scraper.py
```

**Coverage**: All **50 states + DC** configured with verified URLs

**Options**:
1. List all states and their configurations
2. Scrape all states (automated + manual instructions)  
3. Scrape only automated states (~37 states)
4. Scrape specific state
5. Test mode (5 sections per state)

**State Categories**:
- **✓ Automated** (~37 states): Direct scraping works (NY, TX, FL, GA, etc.)
- **⚠ Manual** (~14 states): Requires PDF download or navigation (CA, AL, TN, etc.)

**Manual intervention states**:
States marked as "manual" will generate `MANUAL_DOWNLOAD_INSTRUCTIONS.json` with:
- Download URLs
- Step-by-step instructions
- Tax code references
- Output directory paths

**Key states for testing** (recommended priority):
1. New York (excellent online access)
2. Texas (no income tax - sales/property focus)
3. California (largest economy - manual download)
4. Florida (no income tax - corporate/sales focus)
5. Illinois (structured online access)

**Output**: `data/raw/states/[state_name]/`

**See**: [STATE_TAX_CODES.md](STATE_TAX_CODES.md) for complete state-by-state documentation

### Step 1.3: Download COLIEE Benchmark (Manual)
1. Register at http://coliee.org/
2. Download COLIEE legal retrieval task data
3. Place in `data/raw/benchmark/coliee/`

---

## Phase 2: Scenario Generation (Automated)

```bash
python scenarios/scenario_generator.py
```

**Configuration**:
- Number of scenarios (recommended: 100-200 for pilot, 500+ for full evaluation)
- Tax years to cover (default: 2020-2025)
- Complexity distribution (default: 30% simple, 50% moderate, 20% complex)

**Output**: `data/processed/scenarios/scenarios.jsonl`

**Manual review**:
1. Review sample scenarios for realism
2. Add edge cases manually
3. Ensure jurisdiction coverage

---

## Phase 3: Annotation (Manual-Intensive)

### Step 3.1: Retrieval Annotation
```bash
python annotation/retrieval_annotator.py
```

This starts a web interface at http://localhost:5000

**For each scenario, annotate**:
- All relevant code sections
- Relevance grades (1-3)
- Most controlling section
- Mandatory sections (cannot miss)

**Time estimate**: 5-10 minutes per scenario → 8-17 hours for 100 scenarios

**Tips**:
- Use legal search tools to find relevant sections
- Annotate in batches (10-20 scenarios per session)
- Take breaks to maintain quality

**Output**: `data/annotations/retrieval_gold.json`

### Step 3.2: Extraction Annotation
```bash
# First, create example and guidelines
python annotation/extraction_annotator.py
```

This creates:
- `data/annotations/extraction_example.json` (reference)
- `data/annotations/EXTRACTION_GUIDELINES.md` (instructions)

**Manual process**:
1. Read the guidelines thoroughly
2. Use the example as a template
3. Annotate in JSON format (or build custom tool)
4. For each relevant section, extract:
   - Condition spans
   - Exception spans
   - Numeric values (with units, periods)
   - Dates (effective dates, deadlines)
   - Evidence spans

**Time estimate**: 20-40 minutes per section → 33-67 hours for 100 sections

**Quality control**:
- Do 10-section pilot first
- Check inter-annotator agreement (need >80%)
- Have expert review 10% sample

**Output**: `data/annotations/extraction_gold.json`

### Step 3.3: Reasoning Annotation

For each scenario, manually determine:
- Applicable jurisdictions and tax types
- Required tax forms
- Filing deadlines
- Expected outcomes

**Format**: JSON following this schema:
```json
{
  "scenario_id": "scenario_0001",
  "applicable_jurisdictions": ["US", "CA"],
  "applicable_tax_types": ["income_individual"],
  "required_forms": ["1040", "540"],
  "filing_deadline": "2024-04-15",
  "expected_outcome": {
    "filing_required": true,
    "forms": ["1040", "540"],
    "notes": "Standard filing for CA resident"
  }
}
```

**Time estimate**: 15-30 minutes per scenario → 25-50 hours for 100 scenarios

**Output**: `data/annotations/reasoning_gold.jsonl`

---

## Phase 4: Evaluation (After System Implementation)

### Run Evaluation Metrics
```python
from evaluation.metrics import EvaluationRunner

runner = EvaluationRunner(
    gold_file='data/annotations/retrieval_gold.json',
    predictions_file='predictions/my_system_predictions.json'
)

report = runner.generate_report('evaluation_report.json')
```

### Metrics Computed

**Retrieval**:
- Recall@{5,10,50}
- nDCG@{10,50}
- MRR
- No-miss rate@{5,10,50}
- Per-jurisdiction breakdown
- Macro-averaged across jurisdictions

**Extraction**:
- Span-level F1 (conditions, exceptions, definitions)
- Numeric accuracy (exact match, MAE, unit correctness)
- Date correctness (exact + partial match)
- Attribution precision/recall

**Reasoning**:
- Applicability accuracy
- Form/deadline F1
- Brier score (calibration)
- Expected Calibration Error (ECE)

---

## Manual Intervention Summary

### Required Manual Steps

1. **State Tax Code Collection** (1-2 days)
   - Download PDFs for California
   - Handle special state formats
   - Verify jurisdiction metadata

2. **COLIEE Benchmark** (1 hour)
   - Register and download

3. **Retrieval Annotation** (8-17 hours for 100 scenarios)
   - Use web tool to label relevant sections
   - Requires legal knowledge

4. **Extraction Annotation** (33-67 hours for 100 sections)
   - Detailed span annotation
   - Requires legal + technical expertise
   - **Can outsource to law students**

5. **Reasoning Annotation** (25-50 hours for 100 scenarios)
   - Determine correct answers
   - Requires tax professional
   - **Can outsource to tax professionals**

### Optional Automation Improvements

- Build custom web interface for extraction (similar to retrieval tool)
- Use OCR for PDF-only state codes
- Pre-populate annotations with weak supervision
- Use active learning to reduce annotation burden

---

## Total Time & Cost Estimates

### Do-It-Yourself (100 scenarios)
- Scraping automation: 4-8 hours development + 2-4 hours runtime
- Scenario generation: 2 hours
- Manual data collection: 2-3 days
- Annotation: 66-134 hours
- **Total: ~140-280 hours**

### With Outsourcing (100 scenarios)
- Your time (setup): 10-15 hours
- Law student annotation: 100 hours @ $25-40/hr = $2,500-4,000
- Tax professional review: 15 hours @ $100-200/hr = $1,500-3,000
- **Total cost: $4,000-7,000**
- **Your time: 10-15 hours**

### Full Scale (500 scenarios)
- Your time: 20-30 hours
- Annotation: $20,000-35,000 (outsourced)
- Or 700-1,400 hours DIY

---

## Data Storage Structure

```
data/
├── raw/
│   ├── federal/
│   │   ├── usc_title26/          # IRC sections (automated)
│   │   └── irs_publications/      # IRS pubs (automated)
│   ├── states/
│   │   ├── california/            # CA tax code (manual PDFs)
│   │   ├── new_york/              # NY tax law (automated)
│   │   └── ...
│   └── benchmark/
│       └── coliee/                # COLIEE data (manual download)
├── processed/
│   ├── scenarios/                 # Generated scenarios
│   │   ├── scenarios.jsonl
│   │   └── scenario_summary.json
│   └── cleaned/                   # Cleaned statute text
├── annotations/
│   ├── retrieval_gold.json        # Retrieval labels (manual)
│   ├── extraction_gold.json       # Extraction labels (manual)
│   └── reasoning_gold.jsonl       # Reasoning labels (manual)
└── metadata/
    ├── jurisdictions.json
    └── geocoding.json
```

---

## Quality Control Checklist

- [ ] Federal code: Verify at least 100 sections scraped
- [ ] State codes: 3-5 states minimum
- [ ] Scenarios: Review 10% sample for realism
- [ ] Retrieval annotations: Inter-annotator agreement >80% on 20-scenario pilot
- [ ] Extraction annotations: Expert review 10% sample
- [ ] Reasoning annotations: Cross-check against official IRS publications
- [ ] Test evaluation pipeline on small sample before full run

---

## Troubleshooting

### Scraping Issues
- **Rate limiting**: Increase `rate_limit` parameter
- **CAPTCHA**: Solve manually, then resume with `--resume` flag
- **PDF extraction fails**: Try alternative tools (pdfplumber vs camelot)

### Annotation Issues
- **Low agreement**: Refine guidelines, do training session
- **Tools too slow**: Build custom lightweight interface
- **Missing context**: Include broader statute context in annotation view

---

## Next Steps After Data Collection

1. **Pilot evaluation** (20 scenarios)
   - Test full pipeline
   - Identify gaps in gold labels
   - Refine metrics

2. **Baseline systems**
   - BM25 retrieval
   - Simple regex extraction
   - Rule-based reasoning

3. **Your system**
   - Implement retrieval, extraction, reasoning
   - Iterate based on evaluation

4. **Comparison**
   - Run baselines vs your system
   - Compute all metrics
   - Statistical significance testing (bootstrap)

5. **Analysis**
   - Error taxonomy
   - Per-jurisdiction breakdown
   - Complexity stratification

---

## Citation

If you use this data collection framework, please link back to this repository and cite the relevant benchmarks:

- COLIEE: http://coliee.org/
- Legal IR: Appropriate legal IR papers

---

## Contact & Support

For questions about this data collection plan, open an issue or refer to:
- `DATA_COLLECTION_PLAN.md` for overview
- Individual script files for detailed documentation
- `annotation/EXTRACTION_GUIDELINES.md` for annotation standards
