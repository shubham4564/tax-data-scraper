# Manual Intervention Quick Reference

## Overview
This document lists all manual steps required in the data collection process, organized by urgency and effort.

---

## Critical Manual Steps (Must Do)

### 1. California Tax Code Download (30 min - 1 hour)
**When**: After running state scraper  
**Why**: California's site doesn't allow automated scraping  
**How**:
1. Visit https://www.ftb.ca.gov/tax-pros/law/
2. Download "Revenue and Taxation Code" sections
3. Alternative: https://leginfo.legislature.ca.gov/faces/codes.xhtml
4. Save PDFs to `data/raw/states/california/`

**Files needed**:
- Revenue and Taxation Code (all divisions)
- Focus on: Personal Income Tax (Part 10), Corporation Tax (Part 11), Sales Tax (Division 2)

---

### 2. COLIEE Benchmark Download (1 hour)
**When**: Before evaluation  
**Why**: Needed for baseline comparisons  
**How**:
1. Go to http://coliee.org/
2. Register for dataset access
3. Download "Legal Information Retrieval" task data
4. Extract to `data/raw/benchmark/coliee/`

---

### 3. Retrieval Annotation (8-17 hours for 100 scenarios)
**When**: After scenarios are generated  
**Why**: Creates gold standard for retrieval evaluation  
**How**:
```bash
python annotation/retrieval_annotator.py
# Opens web interface at http://localhost:5000
```

**For each scenario**:
- [ ] Find all relevant statute sections (use legal search)
- [ ] Assign relevance grade (1=marginal, 2=relevant, 3=highly relevant)
- [ ] Mark most controlling section
- [ ] Mark mandatory sections (cannot miss)

**Tips**:
- Work in batches of 10-20 scenarios
- Keep legal reference materials open
- Save frequently
- Target: 5-10 minutes per scenario

---

### 4. Extraction Annotation (33-67 hours for 100 sections)
**When**: After retrieval annotation  
**Why**: Creates gold standard for extraction evaluation  

**Setup**:
```bash
python annotation/extraction_annotator.py
# Creates example and guidelines
```

**Read first**:
- `data/annotations/EXTRACTION_GUIDELINES.md`
- `data/annotations/extraction_example.json`

**For each section, extract**:
- [ ] Condition spans (eligibility, thresholds, requirements)
- [ ] Exception spans (exclusions, limitations)
- [ ] Numeric values (with units: dollar/percent, periods: annual/monthly)
- [ ] Dates (effective dates, deadlines)
- [ ] Definitions
- [ ] Evidence spans (supporting text)

**Annotation format** (JSON):
```json
{
  "section_id": "26-USC-61",
  "extractions": {
    "conditions": [{
      "span_start": 52,
      "span_end": 110,
      "text": "Except as otherwise provided",
      "condition_type": "exclusion"
    }],
    "numeric_values": [{
      "value": 12950,
      "unit": "dollar",
      "period": "annual",
      "scope": "individual"
    }]
  }
}
```

**Tips**:
- Use text editor with line numbers
- Or build custom annotation UI
- Do 5-section pilot first
- Check inter-annotator agreement (aim for >80%)
- **Consider outsourcing to law students** ($25-40/hr)

---

### 5. Reasoning Annotation (25-50 hours for 100 scenarios)
**When**: After extraction annotation  
**Why**: Creates gold standard for end-to-end evaluation  

**For each scenario, determine**:
- [ ] Applicable jurisdictions (federal, state, local)
- [ ] Applicable tax types
- [ ] Required forms (e.g., "1040", "Schedule A")
- [ ] Filing deadlines
- [ ] Expected outcome (filing required? estimated tax?)

**Annotation format** (JSONL):
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
    "notes": "Standard CA resident filing"
  }
}
```

**Save to**: `data/annotations/reasoning_gold.jsonl`

**Tips**:
- Cross-reference with IRS publications
- Use tax preparation software for validation
- **Consider hiring tax professional** ($100-200/hr for review)

---

## Optional Manual Steps

### 6. Handle CAPTCHA During Scraping
**When**: If encountered during federal/state scraping  
**How**: 
- Script will pause
- Solve CAPTCHA in browser
- Press Enter in terminal to continue

---

### 7. PDF Text Extraction Issues
**When**: State PDFs don't extract cleanly  
**How**:
- Try alternative tools: pdfplumber vs camelot
- Use OCR if scanned PDFs: `pip install pytesseract`
- Worst case: Manual copy-paste

---

### 8. Add Custom Scenarios
**When**: After auto-generation  
**Why**: Cover edge cases not in templates  
**How**: Edit `data/processed/scenarios/scenarios.jsonl` and add:

```json
{
  "scenario_id": "scenario_custom_001",
  "jurisdiction": "New York City",
  "tax_type": "income",
  "query": "NYC resident working remotely for CA company...",
  ...
}
```

---

## Outsourcing Strategy

### What to Outsource
1. **Extraction Annotation** → Law students
   - Clear guidelines provided
   - 33-67 hours @ $25-40/hr = $825-2,680

2. **Reasoning Annotation** → Tax professionals
   - 25-50 hours @ $100-200/hr = $2,500-10,000
   - Or: Review only (10 hours) = $1,000-2,000

### What to Keep In-House
1. Scraper development and debugging
2. Scenario generation and curation
3. Quality control and validation
4. Pilot annotation (to create guidelines)

---

## Quality Control Checklist

### Data Collection
- [ ] Federal code: ≥100 sections scraped
- [ ] State codes: ≥3 states
- [ ] Scenarios: 100-500 generated
- [ ] Scenarios reviewed for realism (10% sample)

### Annotation Quality
- [ ] Retrieval pilot: 20 scenarios, 2 annotators, check agreement
- [ ] Agreement >80%? If not, refine guidelines
- [ ] Extraction pilot: 10 sections, expert review
- [ ] Reasoning: Cross-check 10% with IRS publications

### Before Evaluation
- [ ] All annotations in correct format
- [ ] No missing required fields
- [ ] Gold labels cover all test scenarios
- [ ] Evaluation scripts tested on small sample

---

## Time-Saving Tips

1. **Batch similar tasks**: Annotate similar scenarios together
2. **Use templates**: Copy-paste common patterns
3. **Automate validation**: Write scripts to check JSON format
4. **Active learning**: Start with hardest cases, easier ones may be auto-labeled
5. **Parallel work**: Data collection and annotation can overlap

---

## Help & Resources

### Legal Research Tools
- Cornell LII: https://www.law.cornell.edu/
- Justia: https://law.justia.com/
- State legislature websites

### Tax Resources
- IRS Publications: https://www.irs.gov/forms-pubs
- Tax Foundation: https://taxfoundation.org/
- State revenue department websites

### Annotation Tools
- Label Studio: https://labelstud.io/ (if you want pre-built UI)
- Prodigy: https://prodi.gy/ (paid, but powerful)
- Or use the provided Flask tool

---

## Estimated Total Manual Effort

| Task | Time (100 scenarios) | Can Outsource? |
|------|---------------------|----------------|
| CA tax download | 1 hour | No |
| COLIEE download | 1 hour | No |
| Retrieval annotation | 8-17 hours | Partially |
| Extraction annotation | 33-67 hours | Yes ($825-2,680) |
| Reasoning annotation | 25-50 hours | Yes ($2,500-10,000) |
| Quality control | 5-10 hours | No |
| **Total** | **73-146 hours** | **Outsource: ~$3,325-12,680** |

### Cost-Benefit Decision
- **DIY**: Free, but 73-146 hours of your time
- **Partial outsource**: $3,000-10,000, save 50-100 hours
- **Full outsource**: $3,000-12,000, your time: 10-20 hours (QC only)

Choose based on:
- Your time value
- Available budget
- Timeline constraints
- Annotation quality needs
