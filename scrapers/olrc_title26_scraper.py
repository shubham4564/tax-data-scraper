"""
Download structured XML for Title 26 from the Office of the Law Revision Counsel (OLRC).

Outputs:
- data/raw/federal/usc_title26_olrc/xml_usc26@<release>.zip
- data/raw/federal/usc_title26_olrc/xml/ (extracted files)
- data/raw/federal/usc_title26_olrc/sections.jsonl
- data/raw/federal/usc_title26_olrc/summary.json
"""

from __future__ import annotations

import json
import logging
import re
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

import requests
from bs4 import BeautifulSoup


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReleaseInfo:
    release_id: str
    title26_xml_zip_url: str


class OLRCTitle26Scraper:
    """Download and parse Title 26 XML from OLRC release points."""

    DOWNLOAD_PAGE = "https://uscode.house.gov/download/download.shtml"

    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Research/Educational Tax IR System)",
            }
        )
        self.output_dir = Path("data/raw/federal/usc_title26_olrc")
        self.xml_dir = self.output_dir / "xml"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.xml_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> Dict:
        """Execute end-to-end acquisition and section extraction."""
        release = self._discover_current_release()
        zip_path = self._download_title26_zip(release)
        extracted_files = self._extract_zip(zip_path)
        sections = self._parse_sections_from_xml_files(extracted_files)
        self._write_sections(sections)

        summary = {
            "source": "Office of the Law Revision Counsel",
            "download_page": self.DOWNLOAD_PAGE,
            "release_id": release.release_id,
            "zip_url": release.title26_xml_zip_url,
            "zip_path": str(zip_path),
            "xml_files_extracted": len(extracted_files),
            "sections_extracted": len(sections),
            "created_at": datetime.now().isoformat(),
        }

        summary_path = self.output_dir / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        logger.info("OLRC Title 26 acquisition complete. Sections extracted: %d", len(sections))
        return summary

    def _discover_current_release(self) -> ReleaseInfo:
        """Discover current release and Title 26 XML URL from OLRC download page."""
        time.sleep(self.rate_limit)
        response = self.session.get(self.DOWNLOAD_PAGE, timeout=60)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        title_link = soup.find("a", href=re.compile(r"xml_usc26@\d+-\d+\.zip"))
        if not title_link or not title_link.get("href"):
            raise RuntimeError("Could not find Title 26 XML download link on OLRC page")

        title26_url = title_link["href"]
        title26_url = urljoin(self.DOWNLOAD_PAGE, title26_url)

        match = re.search(r"@(?P<release>\d+-\d+)\.zip$", title26_url)
        release_id = match.group("release") if match else "unknown"

        logger.info("Detected OLRC release %s", release_id)
        return ReleaseInfo(release_id=release_id, title26_xml_zip_url=title26_url)

    def _download_title26_zip(self, release: ReleaseInfo) -> Path:
        """Download Title 26 XML zip archive."""
        filename = f"xml_usc26@{release.release_id}.zip"
        zip_path = self.output_dir / filename

        if zip_path.exists() and zip_path.stat().st_size > 0:
            logger.info("Using existing archive %s", zip_path)
            return zip_path

        time.sleep(self.rate_limit)
        response = self.session.get(release.title26_xml_zip_url, stream=True, timeout=120)
        response.raise_for_status()

        with open(zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        logger.info("Downloaded %s", zip_path)
        return zip_path

    def _extract_zip(self, zip_path: Path) -> List[Path]:
        """Extract zip archive into xml directory."""
        extracted_paths: List[Path] = []
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                target = self.xml_dir / Path(member.filename).name
                with zf.open(member, "r") as src, open(target, "wb") as dst:
                    dst.write(src.read())
                extracted_paths.append(target)

        logger.info("Extracted %d files", len(extracted_paths))
        return extracted_paths

    def _parse_sections_from_xml_files(self, xml_files: List[Path]) -> List[Dict]:
        """Parse section-level records from extracted XML files."""
        all_sections: List[Dict] = []

        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
            except ET.ParseError as exc:
                logger.warning("Skipping unparsable XML file %s: %s", xml_file, exc)
                continue

            root = tree.getroot()
            for section in self._find_by_local_name(root, "section"):
                section_number = self._extract_first_text(section, ["num", "enum"]) or "unknown"
                heading = self._extract_first_text(section, ["heading", "chapeau"]) or ""
                text = self._flatten_text(section)

                if not text.strip():
                    continue

                all_sections.append(
                    {
                        "section_number": section_number,
                        "heading": heading,
                        "text": text,
                        "source_file": xml_file.name,
                        "scraped_date": datetime.now().isoformat(),
                    }
                )

        return all_sections

    def _write_sections(self, sections: List[Dict]) -> None:
        """Write consolidated section output files."""
        jsonl_path = self.output_dir / "sections.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for section in sections:
                f.write(json.dumps(section, ensure_ascii=False) + "\n")

    def _find_by_local_name(self, root: ET.Element, local_name: str) -> List[ET.Element]:
        """Find XML elements by local name across any namespace."""
        matches: List[ET.Element] = []
        for elem in root.iter():
            if self._local_name(elem.tag) == local_name:
                matches.append(elem)
        return matches

    def _extract_first_text(self, parent: ET.Element, candidate_names: List[str]) -> Optional[str]:
        """Get the first matching child text by local element names."""
        for elem in parent.iter():
            if self._local_name(elem.tag) in candidate_names:
                text = self._flatten_text(elem).strip()
                if text:
                    return text
        return None

    def _flatten_text(self, elem: ET.Element) -> str:
        """Flatten text nodes preserving rough paragraph boundaries."""
        parts: List[str] = []
        for text in elem.itertext():
            clean = " ".join(text.split())
            if clean:
                parts.append(clean)
        return "\n".join(parts)

    def _local_name(self, tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag


def main() -> None:
    scraper = OLRCTitle26Scraper(rate_limit=1.0)
    summary = scraper.run()
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
