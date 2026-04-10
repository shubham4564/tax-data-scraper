"""Entity and identifier mapping for Phase 4 hybrid retrieval."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from typing import Dict, Iterable, List, Set


TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
FEDERAL_SECTION_RE = re.compile(r"26\s*usc\s*§?\s*([0-9A-Za-z]+)", re.IGNORECASE)
NEVADA_CHAPTER_RE = re.compile(r"(?:nevada|nrs)?\s*chapter\s*([0-9]{1,4}[A-Z]?)", re.IGNORECASE)
STOP_TOKENS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "that",
    "this",
    "these",
    "those",
    "under",
    "chapter",
    "section",
    "subsection",
    "paragraph",
    "title",
    "code",
    "tax",
    "states",
    "state",
    "united",
    "federal",
    "usc",
    "nrs",
}


class Phase4QueryEntityMapper:
    """Maps a query to likely graph entry nodes.

    Strategy:
    1. Hard identifier extraction (federal sections and Nevada chapter references).
    2. Token overlap over heading/identifier text as fallback.
    """

    def __init__(self, nodes: List[Dict]):
        self.nodes = nodes
        self.node_by_id = {node.get("canonical_id", ""): node for node in nodes}
        self.section_lookup = self._build_section_lookup(nodes)
        self.nevada_lookup = self._build_nevada_lookup(nodes)
        self.token_index = self._build_token_index(nodes)
        self.token_df = {token: len(ids) for token, ids in self.token_index.items()}
        self.corpus_size = max(1, len(nodes))

    def map_query_to_nodes(self, query: str, top_k: int = 10, jurisdiction: str | None = None) -> List[str]:
        seeds: List[str] = []

        seeds.extend(self._match_federal_sections(query))
        seeds.extend(self._match_nevada_chapters(query))
        seeds.extend(self._match_rule_based_tax_concepts(query, jurisdiction))

        if len(seeds) < top_k:
            seeds.extend(self._match_by_token_overlap(query, top_k=top_k, jurisdiction=jurisdiction))

        # stable dedupe
        seen: Set[str] = set()
        ordered = []
        for cid in seeds:
            if cid and cid in self.node_by_id and cid not in seen:
                ordered.append(cid)
                seen.add(cid)
            if len(ordered) >= top_k:
                break
        return ordered

    def _match_federal_sections(self, query: str) -> List[str]:
        matches = []
        for raw_section in FEDERAL_SECTION_RE.findall(query or ""):
            section = raw_section.strip()
            if not section:
                continue
            candidates = self.section_lookup.get(section.lower(), [])
            matches.extend(candidates)
        return matches

    def _match_nevada_chapters(self, query: str) -> List[str]:
        matches = []
        for chapter in NEVADA_CHAPTER_RE.findall(query or ""):
            key = chapter.strip().upper()
            matches.extend(self.nevada_lookup.get(key, []))
        return matches

    def _match_rule_based_tax_concepts(self, query: str, jurisdiction: str | None = None) -> List[str]:
        text = (query or "").lower()
        out: List[str] = []

        # Filing status and individual rate schedule.
        if "head of household" in text or "filing status" in text:
            out.extend(self._section_candidates("2", jurisdiction=jurisdiction))

        # Individual income tax obligations and tax imposed baseline.
        if ("individual" in text and "income" in text) or "tax imposed" in text:
            out.extend(self._section_candidates("1", jurisdiction=jurisdiction))

        # Taxable income anchor often co-occurs with rate calculations.
        if "taxable income" in text:
            out.extend(self._section_candidates("63", jurisdiction=jurisdiction))

        # Return filing timing.
        if "filing" in text and "return" in text:
            out.extend(self._section_candidates("6072", jurisdiction=jurisdiction))

        return out

    def _match_by_token_overlap(self, query: str, top_k: int = 10, jurisdiction: str | None = None) -> List[str]:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # Prefer specific query tokens that occur in fewer nodes.
        ranked_query_tokens = sorted(
            query_tokens,
            key=lambda token: (self.token_df.get(token, self.corpus_size), token),
        )[:8]

        scores = defaultdict(float)
        for token in ranked_query_tokens:
            df = self.token_df.get(token, self.corpus_size)
            idf = math.log((self.corpus_size + 1.0) / (df + 1.0)) + 1.0
            for canonical_id in self.token_index.get(token, []):
                if not self._matches_jurisdiction(canonical_id, jurisdiction):
                    continue
                scores[canonical_id] += idf

        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        return [canonical_id for canonical_id, _ in ranked[:top_k]]

    def _section_candidates(self, section: str, jurisdiction: str | None = None) -> List[str]:
        candidates = self.section_lookup.get(section.lower(), [])
        if jurisdiction:
            candidates = [cid for cid in candidates if self._matches_jurisdiction(cid, jurisdiction)]
        # Prefer top-level section nodes first for stable entry points.
        return sorted(candidates, key=lambda cid: ("(" in cid, cid))

    def _matches_jurisdiction(self, canonical_id: str, jurisdiction: str | None) -> bool:
        if not jurisdiction:
            return True
        node = self.node_by_id.get(canonical_id, {})
        node_jurisdiction = (node.get("jurisdiction") or "").lower()
        return node_jurisdiction == jurisdiction.lower()

    def _build_section_lookup(self, nodes: List[Dict]) -> Dict[str, List[str]]:
        lookup: Dict[str, List[str]] = defaultdict(list)
        for node in nodes:
            canonical_id = node.get("canonical_id", "")
            if not canonical_id.startswith("26 USC §"):
                continue
            section_match = re.search(r"26 USC §([0-9A-Za-z]+)", canonical_id)
            if not section_match:
                continue
            section = section_match.group(1).lower()
            lookup[section].append(canonical_id)
        return lookup

    def _build_nevada_lookup(self, nodes: List[Dict]) -> Dict[str, List[str]]:
        lookup: Dict[str, List[str]] = defaultdict(list)
        for node in nodes:
            canonical_id = node.get("canonical_id", "")
            if not canonical_id.startswith("NV NRS Chapter"):
                continue
            match = re.search(r"Chapter\s+([0-9A-Z]+)", canonical_id)
            if match:
                lookup[match.group(1).upper()].append(canonical_id)
        return lookup

    def _build_token_index(self, nodes: List[Dict]) -> Dict[str, Set[str]]:
        index: Dict[str, Set[str]] = defaultdict(set)
        for node in nodes:
            canonical_id = node.get("canonical_id", "")
            text = " ".join(
                [
                    node.get("heading", ""),
                    node.get("identifier_text", ""),
                    node.get("section_id", ""),
                ]
            )
            for token in self._tokenize(text):
                index[token].add(canonical_id)
        return index

    def _tokenize(self, text: str) -> List[str]:
        tokens = []
        for token in TOKEN_RE.findall(text or ""):
            lowered = token.lower()
            if len(lowered) <= 2:
                continue
            if lowered in STOP_TOKENS:
                continue
            tokens.append(lowered)
        return tokens
