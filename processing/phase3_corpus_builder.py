"""Shared Phase 3 corpus builder.

This module unifies the Phase 2 federal hierarchy with Nevada state
chapter records into a single normalized corpus used by both the graph
index and the vector index.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterator, List, Optional, Tuple


@dataclass
class CorpusRecord:
    canonical_id: str
    jurisdiction: str
    source_type: str
    node_type: str
    section_id: str
    node_path: List[str]
    heading: str
    text: str
    identifier_text: str
    content_text: str
    source_path: str
    source_record_id: str
    cross_references: List[Dict]
    metadata: Dict


class Phase3CorpusBuilder:
    def __init__(
        self,
        workspace_root: Path,
        output_dir: Path,
        federal_sections_path: Optional[Path] = None,
        nevada_dir: Optional[Path] = None,
    ):
        self.workspace_root = workspace_root
        self.output_dir = output_dir
        self.federal_sections_path = federal_sections_path or (
            workspace_root / "data" / "processed" / "phase2" / "sections_hierarchy.jsonl"
        )
        self.nevada_dir = nevada_dir or (workspace_root / "data" / "raw" / "states" / "nevada")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build(self) -> Tuple[List[CorpusRecord], Dict]:
        records_by_id: Dict[str, CorpusRecord] = {}
        federal_count = 0
        nevada_count = 0

        for record in self._load_federal_records():
            records_by_id.setdefault(record.canonical_id, record)
            federal_count += 1

        for record in self._load_nevada_records():
            records_by_id.setdefault(record.canonical_id, record)
            nevada_count += 1

        records = list(records_by_id.values())
        records.sort(key=lambda item: (item.jurisdiction, item.canonical_id))

        corpus_path = self.output_dir / "corpus.jsonl"
        with open(corpus_path, "w", encoding="utf-8") as handle:
            for record in records:
                handle.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")

        summary = {
            "corpus_output": str(corpus_path),
            "total_records": len(records),
            "federal_records_seen": federal_count,
            "nevada_records_seen": nevada_count,
            "jurisdiction_counts": self._count_by_jurisdiction(records),
            "generated_at": datetime.now().isoformat(),
        }
        with open(self.output_dir / "corpus_summary.json", "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)

        return records, summary

    def _load_federal_records(self) -> Iterator[CorpusRecord]:
        if not self.federal_sections_path.exists():
            return

        with open(self.federal_sections_path, "r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                payload = json.loads(line)
                section_id = payload.get("canonical_section_id", "")
                heading = payload.get("heading", "")
                cross_references = payload.get("cross_references", [])
                hierarchy = payload.get("hierarchy", {})
                yield from self._flatten_hierarchy(
                    hierarchy=hierarchy,
                    section_id=section_id,
                    heading=heading,
                    cross_references=cross_references,
                    source_path=str(self.federal_sections_path),
                )

    def _flatten_hierarchy(
        self,
        hierarchy: Dict,
        section_id: str,
        heading: str,
        cross_references: List[Dict],
        source_path: str,
        path: Optional[List[str]] = None,
        node_index: int = 0,
    ) -> Iterator[CorpusRecord]:
        path = path or []
        node_type = hierarchy.get("node_type", "")
        normalized_num = hierarchy.get("normalized_num", "")
        current_path = path.copy()
        if node_type != "section" and normalized_num:
            current_path.append(normalized_num)

        canonical_id = section_id + "".join(current_path)
        text = (hierarchy.get("text") or "").strip()
        node_heading = hierarchy.get("heading", "") if node_type != "section" else heading
        identifier_text = self._build_identifier_text("federal", section_id, current_path, node_heading)
        content_text = "\n".join(part for part in [node_heading, text] if part).strip()

        yield CorpusRecord(
            canonical_id=canonical_id,
            jurisdiction="federal",
            source_type="federal_hierarchy",
            node_type=node_type,
            section_id=section_id,
            node_path=current_path,
            heading=node_heading,
            text=text,
            identifier_text=identifier_text,
            content_text=content_text,
            source_path=source_path,
            source_record_id=f"{section_id}#{node_type}:{node_index}",
            cross_references=cross_references if node_type == "section" else [],
            metadata={"path_depth": len(current_path), "has_text": bool(text)},
        )

        child_index = 0
        for child in hierarchy.get("children", []) or []:
            child_index += 1
            yield from self._flatten_hierarchy(
                hierarchy=child,
                section_id=section_id,
                heading=heading,
                cross_references=cross_references,
                source_path=source_path,
                path=current_path,
                node_index=child_index,
            )

    def _load_nevada_records(self) -> Iterator[CorpusRecord]:
        if not self.nevada_dir.exists():
            return

        chapter_files = sorted(self.nevada_dir.glob("chapter_*.json"))
        if not chapter_files:
            generic = self.nevada_dir / "generic_scrape_result.json"
            if generic.exists():
                yield from self._load_nevada_generic(generic)
            return

        for chapter_file in chapter_files:
            payload = self._read_json(chapter_file)
            if not payload:
                continue
            chapter = self._extract_chapter_number(chapter_file.stem)
            if not chapter:
                continue
            title = payload.get("title") or payload.get("heading") or f"Chapter {chapter}"
            text = self._chapter_text(payload, chapter)
            identifier_text = self._build_identifier_text("nevada", chapter, [], title)
            yield CorpusRecord(
                canonical_id=f"NV NRS Chapter {chapter}",
                jurisdiction="nevada",
                source_type="nevada_chapter",
                node_type="chapter",
                section_id=f"NV NRS Chapter {chapter}",
                node_path=[chapter],
                heading=title,
                text=text,
                identifier_text=identifier_text,
                content_text="\n".join(part for part in [title, text] if part).strip(),
                source_path=str(chapter_file),
                source_record_id=chapter_file.name,
                cross_references=[],
                metadata={
                    "chapter": chapter,
                    "sections_found": payload.get("sections_found", 0),
                    "source_url": payload.get("chapter_url", ""),
                },
            )

    def _load_nevada_generic(self, generic_path: Path) -> Iterator[CorpusRecord]:
        payload = self._read_json(generic_path)
        if not payload:
            return
        for item in payload.get("sections", []) or []:
            title = item.get("text", "")
            chapter = self._extract_chapter_number(title)
            if not chapter:
                continue
            identifier_text = self._build_identifier_text("nevada", chapter, [], title)
            yield CorpusRecord(
                canonical_id=f"NV NRS Chapter {chapter}",
                jurisdiction="nevada",
                source_type="nevada_generic",
                node_type="chapter",
                section_id=f"NV NRS Chapter {chapter}",
                node_path=[chapter],
                heading=title,
                text=title,
                identifier_text=identifier_text,
                content_text=title,
                source_path=str(generic_path),
                source_record_id=f"generic:{chapter}",
                cross_references=[],
                metadata={"source_url": item.get("url", "")},
            )

    def _chapter_text(self, payload: Dict, chapter: str) -> str:
        sections = payload.get("sections") or []
        if sections:
            lines = [f"{section.get('text', '').strip()} -> {section.get('url', '').strip()}" for section in sections]
            lines = [line for line in lines if line.strip()]
            if lines:
                return "\n".join(lines)
        return f"Nevada Revised Statutes Chapter {chapter}"

    def _read_json(self, path: Path) -> Optional[Dict]:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def _extract_chapter_number(self, stem_or_text: str) -> str:
        match = re.search(r"(\d+[A-Z]?)", stem_or_text)
        return match.group(1) if match else ""

    def _build_identifier_text(self, jurisdiction: str, section_id: str, node_path: List[str], heading: str) -> str:
        path_text = " ".join(node_path)
        return " ".join(part for part in [jurisdiction, section_id, path_text, heading] if part).strip()

    def _count_by_jurisdiction(self, records: List[CorpusRecord]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for record in records:
            counts[record.jurisdiction] = counts.get(record.jurisdiction, 0) + 1
        return counts


def load_corpus_records(workspace_root: Path, output_dir: Optional[Path] = None) -> Tuple[List[CorpusRecord], Dict]:
    output_dir = output_dir or (workspace_root / "data" / "processed" / "phase3")
    builder = Phase3CorpusBuilder(workspace_root=workspace_root, output_dir=output_dir)
    return builder.build()
