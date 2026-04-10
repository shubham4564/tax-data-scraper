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
import logging
from datetime import datetime
from pathlib import Path

from scrapers.document_text_extractor import DocumentTextExtractor
from scrapers.explanatory_docs_collector import ExplanatoryDocsCollector
from scrapers.olrc_title26_scraper import OLRCTitle26Scraper
from scrapers.state_tax_scraper import StateTaxScraperManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)


def _step(name: str, report: dict, fn):
    """Run a pipeline step, recording success or failure into the report."""
    log.info("Starting step: %s", name)
    try:
        result = fn()
        report["steps"][name] = result
        log.info("Completed step: %s", name)
    except Exception as e:
        log.exception("Step failed: %s", name)
        report["steps"][name] = {"error": str(e), "completed_at": datetime.now().isoformat()}


def main() -> None:
    start = datetime.now()
    report = {
        "started_at": start.isoformat(),
        "steps": {},
    }

    # 1) OLRC Title 26 XML
    olrc = OLRCTitle26Scraper(rate_limit=1.0)
    _step("olrc_title26", report, olrc.run)

    # 2) Nevada official tax chapters
    def nevada_step():
        state_manager = StateTaxScraperManager()
        nevada_records = list(state_manager.scrape_state("nevada"))
        return {
            "records": len(nevada_records),
            "output_dir": "data/raw/states/nevada",
            "completed_at": datetime.now().isoformat(),
        }

    _step("nevada_tax_code", report, nevada_step)

    # 3) Explanatory docs
    collector = ExplanatoryDocsCollector(rate_limit=0.75)
    _step("explanatory_docs", report, lambda: collector.run(start_year=2020, end_year=2026))

    # 4) Text extraction with OCR fallback
    def extraction_step():
        extractor = DocumentTextExtractor(min_direct_chars=500)
        extraction_summary = {}
        for input_dir in [
            Path("data/raw/federal/irs_publications"),
            Path("data/raw/federal/irs_form_instructions"),
        ]:
            if input_dir.exists():
                log.info("Extracting text from: %s", input_dir)
                extraction_summary[str(input_dir)] = extractor.run_directory(input_dir)
            else:
                log.warning("Directory not found, skipping: %s", input_dir)
        return {
            "directories_processed": list(extraction_summary.keys()),
            "summary": extraction_summary,
            "completed_at": datetime.now().isoformat(),
        }

    _step("text_extraction", report, extraction_step)

    finish = datetime.now()
    report["finished_at"] = finish.isoformat()
    report["elapsed_seconds"] = round((finish - start).total_seconds(), 3)

    report_path = Path("data/processed/phase1_acquisition_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    log.info("Report written to %s", report_path)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()