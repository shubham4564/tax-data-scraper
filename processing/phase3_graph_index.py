"""Phase 3 knowledge graph construction."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from processing.phase3_community_summarizer import CommunitySummarizer
from processing.phase3_corpus_builder import CorpusRecord


class Phase3GraphIndex:
    def __init__(self, output_dir: Path, summarizer: Optional[CommunitySummarizer] = None):
        self.output_dir = output_dir
        self.summarizer = summarizer or CommunitySummarizer()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def build(self, records: List[CorpusRecord]) -> Dict:
        node_rows = [self._node_row(record) for record in records]
        node_by_id = {row["canonical_id"]: row for row in node_rows}
        edges = self._build_edges(records, node_by_id)
        communities = self._build_communities(node_rows, edges)

        self._write_jsonl(self.output_dir / "nodes.jsonl", node_rows)
        self._write_jsonl(self.output_dir / "edges.jsonl", edges)
        self._write_jsonl(self.output_dir / "communities.jsonl", communities)

        summary = {
            "total_nodes": len(node_rows),
            "total_edges": len(edges),
            "community_count": len(communities),
            "jurisdiction_counts": self._count_by_jurisdiction(node_rows),
            "generated_at": datetime.now().isoformat(),
        }
        with open(self.output_dir / "graph_summary.json", "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        return summary

    def _node_row(self, record: CorpusRecord) -> Dict:
        return {
            "canonical_id": record.canonical_id,
            "jurisdiction": record.jurisdiction,
            "source_type": record.source_type,
            "node_type": record.node_type,
            "section_id": record.section_id,
            "node_path": record.node_path,
            "heading": record.heading,
            "text": record.text,
            "identifier_text": record.identifier_text,
            "content_text": record.content_text,
            "source_path": record.source_path,
            "source_record_id": record.source_record_id,
            "cross_references": record.cross_references,
            "metadata": record.metadata,
        }

    def _build_edges(self, records: List[CorpusRecord], node_by_id: Dict[str, Dict]) -> List[Dict]:
        edges: List[Dict] = []
        seen = set()
        for record in records:
            parent_id = self._parent_canonical_id(record)
            if parent_id and parent_id in node_by_id:
                edge = (parent_id, record.canonical_id, "hierarchy_parent")
                if edge not in seen:
                    seen.add(edge)
                    edges.append(
                        {
                            "source_node": parent_id,
                            "target_node": record.canonical_id,
                            "edge_type": "hierarchy_parent",
                            "weight": 1.0,
                            "evidence": "node_path",
                            "metadata": {"jurisdiction": record.jurisdiction},
                        }
                    )

            for ref in record.cross_references or []:
                target = ref.get("canonical_target")
                if not target:
                    continue
                edge = (record.canonical_id, target, "cross_reference")
                if edge in seen:
                    continue
                seen.add(edge)
                edges.append(
                    {
                        "source_node": record.canonical_id,
                        "target_node": target,
                        "edge_type": "cross_reference",
                        "weight": 1.0,
                        "evidence": ref.get("text", ""),
                        "metadata": {
                            "href": ref.get("href", ""),
                            "jurisdiction": record.jurisdiction,
                        },
                    }
                )
        return edges

    def _build_communities(self, nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
        adjacency = defaultdict(set)
        for edge in edges:
            if edge["edge_type"] not in {"hierarchy_parent", "cross_reference"}:
                continue
            source = edge["source_node"]
            target = edge["target_node"]
            adjacency[source].add(target)
            adjacency[target].add(source)

        visited = set()
        communities = []
        community_id = 0
        for node in nodes:
            canonical_id = node["canonical_id"]
            if canonical_id in visited:
                continue
            community_id += 1
            stack = [canonical_id]
            component = []
            while stack:
                current = stack.pop()
                if current in visited:
                    continue
                visited.add(current)
                component.append(current)
                for neighbor in adjacency.get(current, set()):
                    if neighbor not in visited:
                        stack.append(neighbor)

            component_nodes = [self._node_lookup(nodes, cid) for cid in component if self._node_lookup(nodes, cid)]
            component_nodes.sort(key=lambda item: (-len(adjacency.get(item["canonical_id"], set())), item["canonical_id"]))
            summary = self.summarizer.summarize(component_nodes[:20])
            communities.append(
                {
                    "community_id": f"community_{community_id}",
                    "size": len(component_nodes),
                    "node_ids": component,
                    "summary": summary,
                    "top_nodes": [node["canonical_id"] for node in component_nodes[:10]],
                }
            )

        return communities

    def _node_lookup(self, nodes: List[Dict], canonical_id: str) -> Optional[Dict]:
        for node in nodes:
            if node["canonical_id"] == canonical_id:
                return node
        return None

    def _parent_canonical_id(self, record: CorpusRecord) -> str:
        if record.jurisdiction == "federal":
            if not record.node_path:
                return ""
            if len(record.node_path) == 1:
                return record.section_id
            parent_path = record.node_path[:-1]
            return record.section_id + "".join(parent_path)

        if record.jurisdiction == "nevada":
            return ""

        return ""

    def _count_by_jurisdiction(self, nodes: List[Dict]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for node in nodes:
            counts[node["jurisdiction"]] = counts.get(node["jurisdiction"], 0) + 1
        return counts

    def _write_jsonl(self, path: Path, rows: List[Dict]) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
