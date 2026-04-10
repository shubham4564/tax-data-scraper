"""Phase 5 condition runner for controlled retrieval ablations."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Literal, Optional

from processing.phase4_hybrid_retriever import Phase4HybridRetriever


Condition = Literal["baseline", "vector_only", "graph_only", "hybrid"]


class Phase5ConditionRunner:
    """Runs one query under a strict retrieval condition."""

    def __init__(self, phase3_dir: Path, model: str = "gpt-5"):
        self.engine = Phase4HybridRetriever(phase3_dir=phase3_dir, model=model)

    def run_query(
        self,
        *,
        query: str,
        jurisdiction: Optional[str],
        condition: Condition,
        k_vector: int = 20,
        k_graph: int = 20,
        k_final: int = 10,
        max_depth: int = 2,
        enable_llm_rerank: bool = True,
    ) -> Dict:
        t0_total = time.perf_counter()
        normalized_jurisdiction = self.engine._normalize_jurisdiction(jurisdiction)

        if condition == "baseline":
            generation = self.engine.generator.generate_baseline(query=query)
            total_ms = (time.perf_counter() - t0_total) * 1000.0
            return {
                "query": query,
                "jurisdiction": normalized_jurisdiction,
                "condition": condition,
                "vector_candidates": [],
                "graph_candidates": [],
                "merged_candidates": [],
                "context": {"context_text": "", "included_ids": [], "words_used": 0, "truncated": False},
                "generation": generation,
                "timing": {
                    "vector_search_ms": 0.0,
                    "graph_traversal_ms": 0.0,
                    "fusion_rerank_ms": 0.0,
                    "context_assembly_ms": 0.0,
                    "generation_ms": total_ms,
                    "total_ms": total_ms,
                },
            }

        t_vector_start = time.perf_counter()
        vector_candidates = self._vector_candidates(
            query=query,
            jurisdiction=normalized_jurisdiction,
            k_vector=k_vector,
        )
        vector_ms = (time.perf_counter() - t_vector_start) * 1000.0

        t_graph_start = time.perf_counter()
        graph_candidates = self._graph_candidates(
            query=query,
            jurisdiction=normalized_jurisdiction,
            vector_candidates=vector_candidates,
            condition=condition,
            k_graph=k_graph,
            max_depth=max_depth,
        )
        graph_ms = (time.perf_counter() - t_graph_start) * 1000.0

        if condition == "vector_only":
            graph_candidates = []
        elif condition == "graph_only":
            vector_candidates = []

        t_fuse_start = time.perf_counter()
        merged = self.engine.reranker.fuse_and_rerank(
            query=query,
            vector_candidates=vector_candidates,
            graph_candidates=graph_candidates,
            top_k=k_final,
            enable_llm_rerank=enable_llm_rerank,
        )
        fuse_ms = (time.perf_counter() - t_fuse_start) * 1000.0

        t_context_start = time.perf_counter()
        broad_query = len(query.split()) > 12
        context_payload = self.engine.context_assembler.assemble(merged, broad_query=broad_query)
        context_ms = (time.perf_counter() - t_context_start) * 1000.0

        t_gen_start = time.perf_counter()
        generation = self.engine.generator.generate(query=query, context_payload=context_payload, ranked_candidates=merged)
        generation_ms = (time.perf_counter() - t_gen_start) * 1000.0

        total_ms = (time.perf_counter() - t0_total) * 1000.0

        return {
            "query": query,
            "jurisdiction": normalized_jurisdiction,
            "condition": condition,
            "vector_candidates": vector_candidates,
            "graph_candidates": graph_candidates,
            "merged_candidates": merged,
            "context": context_payload,
            "generation": generation,
            "timing": {
                "vector_search_ms": vector_ms,
                "graph_traversal_ms": graph_ms,
                "fusion_rerank_ms": fuse_ms,
                "context_assembly_ms": context_ms,
                "generation_ms": generation_ms,
                "total_ms": total_ms,
            },
        }

    def _vector_candidates(self, *, query: str, jurisdiction: Optional[str], k_vector: int) -> List[Dict]:
        vector_results = self.engine.vector_index.search(query=query, k=k_vector, jurisdiction=jurisdiction)
        rows: List[Dict] = []
        for item in vector_results:
            node = item.metadata if isinstance(item.metadata, dict) else {}
            rows.append(
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
        return rows

    def _graph_candidates(
        self,
        *,
        query: str,
        jurisdiction: Optional[str],
        vector_candidates: List[Dict],
        condition: Condition,
        k_graph: int,
        max_depth: int,
    ) -> List[Dict]:
        if condition == "vector_only":
            return []

        seed_nodes = self.engine.entity_mapper.map_query_to_nodes(query, top_k=8, jurisdiction=jurisdiction)
        if not seed_nodes and vector_candidates:
            seed_nodes = [item["canonical_id"] for item in vector_candidates[:3]]

        if not seed_nodes:
            return []

        return self.engine.graph_traverser.traverse(
            start_nodes=seed_nodes,
            max_depth=max_depth,
            max_width=max(4, k_graph // 3),
        )[:k_graph]
