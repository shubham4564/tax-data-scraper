"""
Phase 1 data acquisition runner.

Implements:
1. Statutory Data: OLRC Title 26 structured XML.
2. State Data: Nevada tax code chapters from official NRS registry.
3. Explanatory Documents: IRS publications, IRS form instructions, curated third-party sources.
4. Extraction: Direct PDF text extraction with OCR fallback.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from scrapers.document_text_extractor import DocumentTextExtractor
from scrapers.explanatory_docs_collector import ExplanatoryDocsCollector
from scrapers.olrc_title26_scraper import OLRCTitle26Scraper
from scrapers.state_tax_scraper import StateTaxScraperManager


def main() -> None:
    report = {
        "started_at": datetime.now().isoformat(),
        "steps": {},
    }

    # 1) OLRC Title 26 XML
    olrc = OLRCTitle26Scraper(rate_limit=1.0)
    report["steps"]["olrc_title26"] = olrc.run()

    # 2) Nevada official tax chapters
    state_manager = StateTaxScraperManager()
    nevada_records = state_manager.scrape_state("nevada")
    report["steps"]["nevada_tax_code"] = {
        "records": len(nevada_records),
        "output_dir": "data/raw/states/nevada",
        "completed_at": datetime.now().isoformat(),
    }

    # 3) Explanatory docs
    collector = ExplanatoryDocsCollector(rate_limit=0.75)
    report["steps"]["explanatory_docs"] = collector.run(start_year=2020, end_year=2026)

    # 4) Text extraction with OCR fallback
    extractor = DocumentTextExtractor(min_direct_chars=500)
    extraction_summary = {}
    for input_dir in [
        Path("data/raw/federal/irs_publications"),
        Path("data/raw/federal/irs_form_instructions"),
    ]:
        if input_dir.exists():
            extraction_summary[str(input_dir)] = extractor.run_directory(input_dir)

    report["steps"]["text_extraction"] = {
        "directories_processed": list(extraction_summary.keys()),
        "completed_at": datetime.now().isoformat(),
    }

    report["finished_at"] = datetime.now().isoformat()

    report_path = Path("data/processed/phase1_acquisition_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
