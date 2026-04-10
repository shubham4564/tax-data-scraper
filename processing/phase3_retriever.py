"""Unified retrieval interface for the Phase 3 indexes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from processing.phase3_vector_index import DualVectorIndex


class Phase3Retriever:
    def __init__(self, phase3_dir: Path):
        self.phase3_dir = phase3_dir
        self.vector_index = DualVectorIndex(phase3_dir / "vector")
        self.vector_index.load()
        self.graph_nodes = self._load_jsonl(phase3_dir / "graph" / "nodes.jsonl")
        self.communities = self._load_jsonl(phase3_dir / "graph" / "communities.jsonl")
        self.node_map = {node["canonical_id"]: node for node in self.graph_nodes}
        self.community_map = self._build_community_map()

    def search(self, query: str, k: int = 10, jurisdiction: Optional[str] = None) -> List[Dict]:
        results = self.vector_index.search(query=query, k=k, jurisdiction=jurisdiction)
        enriched = []
        for result in results:
            node = self.node_map.get(result.canonical_id, {})
            community_id = self.community_map.get(result.canonical_id)
            enriched.append(
                {
                    "canonical_id": result.canonical_id,
                    "score": result.score,
                    "content_score": result.content_score,
                    "identifier_score": result.identifier_score,
                    "jurisdiction": node.get("jurisdiction"),
                    "heading": node.get("heading"),
                    "node_type": node.get("node_type"),
                    "community_id": community_id,
                    "graph_expansion": self._graph_expansion(result.canonical_id),
                }
            )
        return enriched

    def _graph_expansion(self, canonical_id: str) -> Dict:
        neighbors = []
        node = self.node_map.get(canonical_id)
        if not node:
            return {"neighbors": neighbors, "community_summary": ""}
        for other in self.graph_nodes:
            if other["canonical_id"] == canonical_id:
                continue
            if other.get("section_id") == node.get("section_id") and other.get("jurisdiction") == node.get("jurisdiction"):
                if other.get("node_type") != "section":
                    neighbors.append(other["canonical_id"])
            if len(neighbors) >= 5:
                break
        community_id = self.community_map.get(canonical_id)
        community_summary = ""
        for community in self.communities:
            if community.get("community_id") == community_id:
                community_summary = community.get("summary", "")
                break
        return {"neighbors": neighbors, "community_summary": community_summary}

    def _build_community_map(self) -> Dict[str, str]:
        mapping = {}
        for community in self.communities:
            community_id = community.get("community_id")
            for node_id in community.get("node_ids", []):
                mapping[node_id] = community_id
        return mapping

    def _load_jsonl(self, path: Path) -> List[Dict]:
        rows = []
        if not path.exists():
            return rows
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows
