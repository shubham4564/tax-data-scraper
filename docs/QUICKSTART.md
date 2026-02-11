# Quick Start - 5-Minute Setup

Get started with data collection in 5 minutes:

## 1. Install Dependencies (2 min)
```bash
cd "Code"
pip install -r requirements.txt
```

## 2. Test Federal Scraper (2 min)
```bash
python scrapers/federal_tax_scraper.py
# Choose option 2 (test mode - 20 sections)
# OR choose option 3 for comprehensive 280+ section coverage (5 min)
```

Expected output: `data/raw/federal/usc_title26/section_*.json`

**Note**: The scraper includes 280+ IRC sections covering all major tax areas. See [IRC_SECTION_COVERAGE.md](IRC_SECTION_COVERAGE.md) for complete documentation.

## 3. Generate Sample Scenarios (1 min)
```bash
python scenarios/scenario_generator.py
# Enter 10 when asked for number of scenarios
```

Expected output: `data/processed/scenarios/scenarios.jsonl`

---

## Next: Choose Your Path

### Path A: Full Automation (Your Time: ~20 hours)
```bash
# Run the orchestrator
python run_data_collection.py

# Follow the guided prompts
# Do all manual steps yourself
```

**Timeline**: 2-3 weeks  
**Cost**: $0  
**Best for**: Learning, full control

### Path B: Partial Outsourcing (Your Time: ~30 hours + $3-7k)
```bash
# Run orchestrator for automated steps
python run_data_collection.py
# Complete steps 1-4

# Do retrieval annotation yourself
python annotation/retrieval_annotator.py

# Outsource extraction to law students
# Outsource reasoning to tax professional
```

**Timeline**: 2-3 weeks  
**Cost**: $3,000-7,000  
**Best for**: Balanced approach

### Path C: Maximum Outsourcing (Your Time: ~15 hours + $10-15k)
```bash
# Setup only
python run_data_collection.py
# Complete automated steps only

# Outsource all annotation work
# You do: quality control + validation
```

**Timeline**: 1-2 weeks  
**Cost**: $10,000-15,000  
**Best for**: Fast results, large budget

---

## Verification Checklist

After setup, verify:

- [ ] `requirements.txt` installed without errors
- [ ] Test scraper created files in `data/raw/federal/`
- [ ] Scenario generator created `scenarios.jsonl`
- [ ] You can access `http://localhost:5000` when running retrieval annotator

---

## Common First-Time Issues

**Issue**: `ModuleNotFoundError: No module named 'requests'`  
**Fix**: Run `pip install -r requirements.txt`

**Issue**: Scraper returns 403/blocked  
**Fix**: Increase `rate_limit=2.0` in scraper code

**Issue**: Can't access annotation tool at localhost:5000  
**Fix**: Check if port 5000 is available, or change port in code

**Issue**: No data files created  
**Fix**: Check file paths are absolute, directories exist

---

## What to Expect

### After Full Setup (100 scenarios):

**Data Size**:
- Raw statutes: 50-200 MB
- Scenarios: <1 MB  
- Annotations: 5-20 MB
- Total: ~100-300 MB

**Files**:
- 100-500 statute section files
- 100-200 scenario files
- 3 annotation files (retrieval, extraction, reasoning)

**Time Investment**:
- Automation: 10-20 hours (development + monitoring)
- Manual: 70-150 hours (annotation)
- Or outsource: $3,000-15,000

---

## Your First Session (30 min)

Recommended first session workflow:

```bash
# Install (5 min)
pip install -r requirements.txt

# Test federal scraper (10 min)
python scrapers/federal_tax_scraper.py
# Choose test mode (option 2)

# Generate scenarios (5 min)
python scenarios/scenario_generator.py
# Generate 10 scenarios

# Start retrieval annotation (10 min)
python annotation/retrieval_annotator.py
# Annotate 2-3 scenarios to get a feel

# Review outputs
ls data/raw/federal/usc_title26/
cat data/processed/scenarios/scenarios.jsonl | head
```

At the end, you'll have:
- ✓ Working scrapers
- ✓ Sample data
- ✓ Understanding of annotation process
- ✓ Confidence to scale up

---

## Ready to Begin?

```bash
# Start here:
python run_data_collection.py
```

Or jump to specific component:
- Federal scraping: `python scrapers/federal_tax_scraper.py`
- State scraping: `python scrapers/state_tax_scraper.py`  
- Scenarios: `python scenarios/scenario_generator.py`
- Annotation: `python annotation/retrieval_annotator.py`

---

## Need Help?

1. Check [README.md](README.md) for complete guide
2. See [MANUAL_STEPS.md](MANUAL_STEPS.md) for manual task reference
3. Review [DATA_COLLECTION_PLAN.md](DATA_COLLECTION_PLAN.md) for strategy
4. Read inline code documentation

Good luck! 🚀
