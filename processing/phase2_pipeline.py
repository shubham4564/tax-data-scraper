"""
Phase 2 processing and pairing pipeline.

Implements:
1. XML Parsing with hierarchy preservation.
2. Cross-reference extraction from <ref> tags.
3. Canonical normalization + chunking.
4. Pairing statute chunks with explanatory text chunks.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from xml.etree import ElementTree as ET


STRUCTURAL_TAGS = {
    "subsection",
    "paragraph",
    "subparagraph",
    "clause",
    "subclause",
    "item",
    "subitem",
}

TEXT_TAGS = {"content", "chapeau", "continuation", "p"}

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


@dataclass
class ExplanatoryChunk:
    chunk_id: str
    source: str
    text: str
    tokens: set


class Phase2Pipeline:
    def __init__(
        self,
        xml_path: Path,
        explanatory_text_dir: Path,
        third_party_dir: Path,
        output_dir: Path,
        max_chunk_chars: int = 1200,
    ):
        self.xml_path = xml_path
        self.explanatory_text_dir = explanatory_text_dir
        self.third_party_dir = third_party_dir
        self.output_dir = output_dir
        self.max_chunk_chars = max_chunk_chars

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, max_sections: Optional[int] = None) -> Dict:
        explanatory_chunks = self._build_explanatory_corpus()

        sections_path = self.output_dir / "sections_hierarchy.jsonl"
        units_path = self.output_dir / "retrieval_units.jsonl"

        sections_written = 0
        chunks_written = 0

        with open(sections_path, "w", encoding="utf-8") as sec_out, open(
            units_path, "w", encoding="utf-8"
        ) as unit_out:
            for section_payload in self._iter_sections(max_sections=max_sections):
                sec_out.write(json.dumps(section_payload, ensure_ascii=False) + "\n")
                sections_written += 1

                for chunk in section_payload.get("chunks", []):
                    chunk_pairs = self._pair_with_explanatory(
                        statute_chunk=chunk,
                        explanatory_chunks=explanatory_chunks,
                        top_k=3,
                    )
                    unit = {
                        "retrieval_unit_id": chunk["chunk_id"],
                        "statute": {
                            "canonical_id": chunk["canonical_id"],
                            "section_id": section_payload["canonical_section_id"],
                            "heading": section_payload.get("heading", ""),
                            "node_path": chunk.get("node_path", []),
                            "text": chunk["text"],
                        },
                        "cross_references": section_payload.get("cross_references", []),
                        "paired_explanatory": chunk_pairs,
                        "created_at": datetime.now().isoformat(),
                    }
                    unit_out.write(json.dumps(unit, ensure_ascii=False) + "\n")
                    chunks_written += 1

        summary = {
            "xml_source": str(self.xml_path),
            "sections_output": str(sections_path),
            "retrieval_units_output": str(units_path),
            "sections_processed": sections_written,
            "retrieval_units": chunks_written,
            "explanatory_chunks": len(explanatory_chunks),
            "generated_at": datetime.now().isoformat(),
        }

        with open(self.output_dir / "summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def _iter_sections(self, max_sections: Optional[int] = None) -> Iterable[Dict]:
        count = 0
        for _, elem in ET.iterparse(self.xml_path, events=("end",)):
            if self._local_name(elem.tag) != "section":
                continue

            identifier = elem.attrib.get("identifier", "")
            if not re.search(r"/us/usc/t26/s", identifier):
                elem.clear()
                continue

            section_num = self._extract_direct_num(elem)
            if not section_num:
                elem.clear()
                continue

            heading = self._extract_direct_text(elem, "heading")
            canonical_section = self._canonical_section(section_num)

            hierarchy = self._build_hierarchy(elem, section_num=section_num)
            cross_refs = self._extract_cross_references(elem)
            chunks = self._chunk_section(hierarchy, canonical_section)

            payload = {
                "section_number": section_num,
                "canonical_section_id": canonical_section,
                "heading": heading,
                "identifier": identifier,
                "hierarchy": hierarchy,
                "cross_references": cross_refs,
                "chunks": chunks,
                "processed_at": datetime.now().isoformat(),
            }

            yield payload

            count += 1
            elem.clear()
            if max_sections and count >= max_sections:
                break

    def _build_hierarchy(self, section_elem: ET.Element, section_num: str) -> Dict:
        root = {
            "node_type": "section",
            "num": section_num,
            "normalized_num": f"{section_num}",
            "heading": self._extract_direct_text(section_elem, "heading"),
            "text": self._collect_direct_text_blocks(section_elem),
            "children": [],
        }

        for child in list(section_elem):
            child_tag = self._local_name(child.tag)
            if child_tag in STRUCTURAL_TAGS:
                root["children"].append(self._build_structural_node(child))

        return root

    def _build_structural_node(self, elem: ET.Element) -> Dict:
        node_type = self._local_name(elem.tag)
        raw_num = self._extract_direct_num(elem)

        node = {
            "node_type": node_type,
            "num": raw_num,
            "normalized_num": self._normalize_subunit_num(raw_num),
            "heading": self._extract_direct_text(elem, "heading"),
            "text": self._collect_direct_text_blocks(elem),
            "children": [],
        }

        for child in list(elem):
            child_tag = self._local_name(child.tag)
            if child_tag in STRUCTURAL_TAGS:
                node["children"].append(self._build_structural_node(child))

        return node

    def _extract_cross_references(self, section_elem: ET.Element) -> List[Dict]:
        refs: List[Dict] = []

        for ref in section_elem.iter():
            if self._local_name(ref.tag) != "ref":
                continue

            href = ref.attrib.get("href", "").strip()
            if not href:
                continue

            target = self._canonical_from_href(href)
            refs.append(
                {
                    "href": href,
                    "text": self._flatten_text(ref),
                    "canonical_target": target,
                }
            )

        return refs

    def _chunk_section(self, hierarchy: Dict, canonical_section: str) -> List[Dict]:
        chunks: List[Dict] = []

        def visit(node: Dict, path: List[str]) -> None:
            current_path = path.copy()
            norm = node.get("normalized_num")
            if node.get("node_type") != "section" and norm:
                current_path.append(norm)

            canonical_id = canonical_section + "".join(current_path)
            text = (node.get("text") or "").strip()
            if text:
                sub_chunks = self._split_long_text(text)
                for idx, sub_text in enumerate(sub_chunks, start=1):
                    chunk_id = f"{canonical_id}#c{idx}"
                    chunks.append(
                        {
                            "chunk_id": chunk_id,
                            "canonical_id": canonical_id,
                            "node_type": node.get("node_type"),
                            "node_path": current_path,
                            "heading": node.get("heading", ""),
                            "text": sub_text,
                        }
                    )

            for child in node.get("children", []):
                visit(child, current_path)

        visit(hierarchy, [])
        return chunks

    def _pair_with_explanatory(
        self,
        statute_chunk: Dict,
        explanatory_chunks: List[ExplanatoryChunk],
        top_k: int = 3,
    ) -> List[Dict]:
        canonical_id = statute_chunk.get("canonical_id", "")
        section_num = self._extract_section_num_from_canonical(canonical_id)
        heading_tokens = self._tokenize(statute_chunk.get("heading", ""))

        scored: List[Tuple[int, ExplanatoryChunk]] = []

        section_pattern = None
        if section_num:
            section_pattern = re.compile(rf"(section|sec\.|§)\s*{re.escape(section_num)}\b", re.IGNORECASE)

        for ex in explanatory_chunks:
            score = 0
            if section_pattern and section_pattern.search(ex.text):
                score += 5

            overlap = len(heading_tokens.intersection(ex.tokens))
            score += overlap

            if score > 0:
                scored.append((score, ex))

        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:top_k]

        return [
            {
                "source": ex.source,
                "chunk_id": ex.chunk_id,
                "score": score,
                "text": ex.text,
            }
            for score, ex in top
        ]

    def _build_explanatory_corpus(self) -> List[ExplanatoryChunk]:
        chunks: List[ExplanatoryChunk] = []

        if self.explanatory_text_dir.exists():
            for txt_file in sorted(self.explanatory_text_dir.glob("*.txt")):
                text = txt_file.read_text(encoding="utf-8", errors="ignore")
                for idx, part in enumerate(self._split_long_text(text), start=1):
                    chunk_id = f"{txt_file.name}#c{idx}"
                    chunks.append(
                        ExplanatoryChunk(
                            chunk_id=chunk_id,
                            source=str(txt_file),
                            text=part,
                            tokens=self._tokenize(part),
                        )
                    )

        if self.third_party_dir.exists():
            for json_file in sorted(self.third_party_dir.glob("*.json")):
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                text = data.get("text", "")
                for idx, part in enumerate(self._split_long_text(text), start=1):
                    chunk_id = f"{json_file.name}#c{idx}"
                    chunks.append(
                        ExplanatoryChunk(
                            chunk_id=chunk_id,
                            source=str(json_file),
                            text=part,
                            tokens=self._tokenize(part),
                        )
                    )

        return chunks

    def _split_long_text(self, text: str) -> List[str]:
        clean = "\n".join(line.strip() for line in text.splitlines() if line.strip())
        if not clean:
            return []

        if len(clean) <= self.max_chunk_chars:
            return [clean]

        paragraphs = [p.strip() for p in clean.split("\n") if p.strip()]
        chunks: List[str] = []
        current = ""

        for para in paragraphs:
            candidate = f"{current}\n{para}".strip() if current else para
            if len(candidate) <= self.max_chunk_chars:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = para

        if current:
            chunks.append(current)

        return chunks

    def _extract_direct_num(self, elem: ET.Element) -> str:
        for child in list(elem):
            if self._local_name(child.tag) == "num":
                value = child.attrib.get("value")
                if value:
                    return value.strip()
                text = self._flatten_text(child)
                if text:
                    return self._clean_num_text(text)
        return ""

    def _extract_direct_text(self, elem: ET.Element, tag_name: str) -> str:
        for child in list(elem):
            if self._local_name(child.tag) == tag_name:
                return self._flatten_text(child)
        return ""

    def _collect_direct_text_blocks(self, elem: ET.Element) -> str:
        parts: List[str] = []

        for child in list(elem):
            child_tag = self._local_name(child.tag)
            if child_tag in TEXT_TAGS:
                text = self._flatten_text(child)
                if text:
                    parts.append(text)

        return "\n".join(parts)

    def _flatten_text(self, elem: ET.Element) -> str:
        parts: List[str] = []
        for t in elem.itertext():
            clean = " ".join(t.split())
            if clean:
                parts.append(clean)
        return " ".join(parts).strip()

    def _clean_num_text(self, raw: str) -> str:
        text = raw.strip()
        text = text.replace("§", "").replace(".", "").strip()
        return text

    def _normalize_subunit_num(self, raw_num: str) -> str:
        if not raw_num:
            return ""
        n = raw_num.strip()
        if n.startswith("(") and n.endswith(")"):
            return n
        return f"({n})"

    def _canonical_section(self, section_num: str) -> str:
        return f"26 USC §{section_num}"

    def _canonical_from_href(self, href: str) -> Optional[str]:
        m = re.search(r"/us/usc/t26/s(?P<section>[0-9A-Za-z]+)(?P<tail>(?:/[0-9A-Za-z]+)*)", href)
        if not m:
            return None

        section = m.group("section")
        tail = m.group("tail") or ""
        parts = [p for p in tail.split("/") if p]
        suffix = "".join(f"({p})" for p in parts)
        return f"26 USC §{section}{suffix}"

    def _extract_section_num_from_canonical(self, canonical_id: str) -> str:
        m = re.search(r"26 USC §([0-9A-Za-z]+)", canonical_id)
        return m.group(1) if m else ""

    def _tokenize(self, text: str) -> set:
        return {t.lower() for t in TOKEN_RE.findall(text) if len(t) > 2}

    def _local_name(self, tag: str) -> str:
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 2 processing and pairing pipeline")
    parser.add_argument(
        "--xml-path",
        default="data/raw/federal/usc_title26_olrc/xml/usc26.xml",
        help="Path to OLRC Title 26 XML file",
    )
    parser.add_argument(
        "--explanatory-text-dir",
        default="data/processed/explanatory_text",
        help="Directory with extracted explanatory text files",
    )
    parser.add_argument(
        "--third-party-dir",
        default="data/raw/explanatory/third_party",
        help="Directory with curated third-party explanatory JSON files",
    )
    parser.add_argument(
        "--output-dir",
        default="data/processed/phase2",
        help="Output directory for phase 2 artifacts",
    )
    parser.add_argument(
        "--max-sections",
        type=int,
        default=None,
        help="Optional cap for faster test runs",
    )

    args = parser.parse_args()

    pipeline = Phase2Pipeline(
        xml_path=Path(args.xml_path),
        explanatory_text_dir=Path(args.explanatory_text_dir),
        third_party_dir=Path(args.third_party_dir),
        output_dir=Path(args.output_dir),
    )

    summary = pipeline.run(max_sections=args.max_sections)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
