"""Graph traversal utilities for Phase 4 hybrid retrieval."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import DefaultDict, Dict, List, Optional, Set


class Phase4GraphTraverser:
    def __init__(self, graph_dir: Path):
        self.graph_dir = graph_dir
        self.nodes = self._read_jsonl(graph_dir / "nodes.jsonl")
        self.edges = self._read_jsonl(graph_dir / "edges.jsonl")
        self.communities = self._read_jsonl(graph_dir / "communities.jsonl")

        self.node_map = {node.get("canonical_id", ""): node for node in self.nodes}
        self.adjacency = self._build_adjacency(self.edges)
        self.community_map = self._build_community_map(self.communities)
        self.community_summary = {
            item.get("community_id", ""): item.get("summary", "") for item in self.communities
        }

    def traverse(
        self,
        start_nodes: List[str],
        max_depth: int = 2,
        max_width: int = 10,
        edge_types: Optional[Set[str]] = None,
    ) -> List[Dict]:
        edge_types = edge_types or {"hierarchy_parent", "cross_reference"}

        queue = deque()
        visited = set()
        candidates = []

        for start in start_nodes:
            if start in self.node_map:
                queue.append((start, 0, "seed"))

        while queue:
            current, depth, via_edge = queue.popleft()
            if current in visited:
                continue
            visited.add(current)

            node = self.node_map.get(current)
            if not node:
                continue

            confidence = 1.0 / (1 + depth)
            community_id = self.community_map.get(current)
            candidates.append(
                {
                    "canonical_id": current,
                    "depth": depth,
                    "graph_score": confidence,
                    "edge_via": via_edge,
                    "community_id": community_id,
                    "community_summary": self.community_summary.get(community_id, ""),
                    "node": node,
                }
            )

            if depth >= max_depth:
                continue

            neighbors = self.adjacency.get(current, [])
            pushed = 0
            for neighbor, edge_type in neighbors:
                if edge_type not in edge_types:
                    continue
                if neighbor in visited:
                    continue
                queue.append((neighbor, depth + 1, edge_type))
                pushed += 1
                if pushed >= max_width:
                    break

        candidates.sort(key=lambda item: (-item["graph_score"], item["canonical_id"]))
        return candidates

    def _build_adjacency(self, edges: List[Dict]) -> DefaultDict[str, List]:
        adjacency: DefaultDict[str, List] = defaultdict(list)
        for edge in edges:
            source = edge.get("source_node")
            target = edge.get("target_node")
            edge_type = edge.get("edge_type", "")
            if not source or not target:
                continue
            adjacency[source].append((target, edge_type))
            adjacency[target].append((source, edge_type))
        return adjacency

    def _build_community_map(self, communities: List[Dict]) -> Dict[str, str]:
        mapping = {}
        for community in communities:
            community_id = community.get("community_id")
            for node_id in community.get("node_ids", []):
                mapping[node_id] = community_id
        return mapping

    def _read_jsonl(self, path: Path) -> List[Dict]:
        rows = []
        if not path.exists():
            return rows
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows
