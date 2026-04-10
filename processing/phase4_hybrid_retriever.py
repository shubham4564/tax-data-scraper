"""Phase 4 hybrid retrieval engine orchestrator."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from processing.phase3_vector_index import DualVectorIndex
from processing.phase4_context_assembler import Phase4ContextAssembler
from processing.phase4_generator import Phase4Generator
from processing.phase4_graph_traverser import Phase4GraphTraverser
from processing.phase4_query_entity_mapper import Phase4QueryEntityMapper
from processing.phase4_reranker import Phase4Reranker


class Phase4HybridRetriever:
    def __init__(self, phase3_dir: Path, model: str = "gpt-4.1-mini"):
        self.phase3_dir = phase3_dir
        self.vector_index = DualVectorIndex(phase3_dir / "vector")
        self.vector_index.load()

        graph_dir = phase3_dir / "graph"
        self.graph_traverser = Phase4GraphTraverser(graph_dir)
        self.entity_mapper = Phase4QueryEntityMapper(self.graph_traverser.nodes)
        self.reranker = Phase4Reranker(model=model)
        self.context_assembler = Phase4ContextAssembler()
        self.generator = Phase4Generator(model=model)

    def infer(
        self,
        query: str,
        jurisdiction: Optional[str] = None,
        k_vector: int = 20,
        k_graph: int = 20,
        k_final: int = 10,
        max_depth: int = 2,
    ) -> Dict:
        normalized_jurisdiction = self._normalize_jurisdiction(jurisdiction)
        vector_results = self.vector_index.search(
            query=query,
            k=k_vector,
            jurisdiction=normalized_jurisdiction,
        )
        vector_candidates = []
        for item in vector_results:
            node = item.metadata if isinstance(item.metadata, dict) else {}
            vector_candidates.append(
                {
                    "canonical_id": item.canonical_id,
                    "vector_score": item.score,
                    "content_score": item.content_score,
                    "identifier_score": item.identifier_score,
                    "node": node,
                    "section_id": node.get("section_id", item.canonical_id),
                    "jurisdiction": node.get("jurisdiction"),
                }
            )

        seed_nodes = self.entity_mapper.map_query_to_nodes(
            query,
            top_k=8,
            jurisdiction=normalized_jurisdiction,
        )
        if not seed_nodes:
            seed_nodes = [item["canonical_id"] for item in vector_candidates[:3]]

        graph_candidates = self.graph_traverser.traverse(
            start_nodes=seed_nodes,
            max_depth=max_depth,
            max_width=max(4, k_graph // 3),
        )[:k_graph]

        merged = self.reranker.fuse_and_rerank(
            query=query,
            vector_candidates=vector_candidates,
            graph_candidates=graph_candidates,
            top_k=k_final,
        )

        broad_query = len(query.split()) > 12
        context_payload = self.context_assembler.assemble(merged, broad_query=broad_query)
        generation = self.generator.generate(query=query, context_payload=context_payload, ranked_candidates=merged)

        return {
            "query": query,
            "jurisdiction": normalized_jurisdiction,
            "vector_candidates": vector_candidates[:k_vector],
            "graph_candidates": graph_candidates,
            "merged_candidates": merged,
            "context": context_payload,
            "generation": generation,
        }

    def _normalize_jurisdiction(self, jurisdiction: Optional[str]) -> Optional[str]:
        if not jurisdiction:
            return None
        text = jurisdiction.strip().lower()
        if text in {"federal", "united states", "us", "usa"}:
            return "federal"
        if text in {"nevada", "nv"}:
            return "nevada"
        return None


def write_jsonl(path: Path, rows: List[Dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
