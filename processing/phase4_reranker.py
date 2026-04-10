"""Fusion and reranking for Phase 4 hybrid retrieval."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from processing.llm_provider_registry import LLMClient


class Phase4Reranker:
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4.1-mini"):
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.llm_client = LLMClient(model)

    def fuse_and_rerank(
        self,
        query: str,
        vector_candidates: List[Dict],
        graph_candidates: List[Dict],
        top_k: int = 10,
        enable_llm_rerank: bool = True,
    ) -> List[Dict]:
        merged = self._fuse_candidates(vector_candidates, graph_candidates)
        prefiltered = self._build_prefiltered_candidates(merged, top_k=top_k)

        llm_ranked = self._llm_rerank(query, prefiltered) if enable_llm_rerank else []
        if llm_ranked:
            llm_score_map = {item["canonical_id"]: item["rerank_score"] for item in llm_ranked}
            for item in prefiltered:
                item["rerank_score"] = llm_score_map.get(item["canonical_id"], 0.0)
            prefiltered.sort(
                key=lambda item: (
                    -item.get("rerank_score", 0.0),
                    -item.get("fusion_score", 0.0),
                    item.get("canonical_id", ""),
                )
            )
        else:
            for item in prefiltered:
                item["rerank_score"] = item["fusion_score"]

        return prefiltered[:top_k]

    def _diversify_by_section(self, ranked: List[Dict], top_k: int) -> List[Dict]:
        if not ranked:
            return []

        selected: List[Dict] = []
        used_sections = set()

        # First pass: prefer one high-quality result per section.
        for item in ranked:
            section_id = self._section_key(item)
            if section_id in used_sections:
                continue
            selected.append(item)
            used_sections.add(section_id)
            if len(selected) >= top_k:
                return selected

        # Second pass: fill remaining slots by score order.
        used_ids = {item.get("canonical_id", "") for item in selected}
        for item in ranked:
            cid = item.get("canonical_id", "")
            if cid in used_ids:
                continue
            selected.append(item)
            if len(selected) >= top_k:
                break
        return selected

    def _section_key(self, item: Dict) -> str:
        node = item.get("node") if isinstance(item.get("node"), dict) else {}
        section_id = node.get("section_id") or item.get("section_id") or item.get("canonical_id", "")
        return str(section_id)

    def _build_prefiltered_candidates(self, merged: List[Dict], top_k: int) -> List[Dict]:
        target = max(top_k * 3, top_k)
        prefiltered = list(merged[: max(top_k * 2, top_k)])
        seen = {item.get("canonical_id", "") for item in prefiltered}

        # Always keep strong graph-relevant candidates in the rerank pool.
        graph_ranked = sorted(
            merged,
            key=lambda item: (-item.get("graph_score", 0.0), -item.get("fusion_score", 0.0), item.get("canonical_id", "")),
        )
        for item in graph_ranked:
            cid = item.get("canonical_id", "")
            if not cid or cid in seen:
                continue
            prefiltered.append(item)
            seen.add(cid)
            if len(prefiltered) >= target:
                break

        return prefiltered[:target]

    def _fuse_candidates(self, vector_candidates: List[Dict], graph_candidates: List[Dict]) -> List[Dict]:
        by_id: Dict[str, Dict] = {}

        max_vector = max((item.get("vector_score", 0.0) for item in vector_candidates), default=1.0) or 1.0
        max_graph = max((item.get("graph_score", 0.0) for item in graph_candidates), default=1.0) or 1.0

        for item in vector_candidates:
            canonical_id = item.get("canonical_id", "")
            if not canonical_id:
                continue
            row = by_id.setdefault(canonical_id, {"canonical_id": canonical_id})
            row.update(item)
            row["vector_score"] = item.get("vector_score", 0.0) / max_vector
            row.setdefault("graph_score", 0.0)

        for item in graph_candidates:
            canonical_id = item.get("canonical_id", "")
            if not canonical_id:
                continue
            row = by_id.setdefault(canonical_id, {"canonical_id": canonical_id})
            row.update(item)
            row["graph_score"] = max(row.get("graph_score", 0.0), item.get("graph_score", 0.0) / max_graph)
            row.setdefault("vector_score", 0.0)

        merged = []
        for item in by_id.values():
            vector_score = item.get("vector_score", 0.0)
            graph_score = item.get("graph_score", 0.0)
            both_signal_bonus = 0.1 * min(vector_score, graph_score)
            seed_bonus = 0.05 if item.get("edge_via") == "seed" else 0.0
            if graph_score <= 0.0:
                # Vector-only hits are often semantically broad in legal corpora; keep as weak backfill only.
                fusion = 0.12 * vector_score
            else:
                fusion = 0.3 * vector_score + 0.7 * graph_score + both_signal_bonus + seed_bonus
            item["fusion_score"] = fusion
            merged.append(item)

        merged.sort(key=lambda item: (-item.get("fusion_score", 0.0), item.get("canonical_id", "")))
        return merged

    def _llm_rerank(self, query: str, candidates: List[Dict]) -> List[Dict]:
        if not candidates:
            return []

        if not self._is_provider_available():
            return []

        compact_rows = []
        for candidate in candidates[:25]:
            compact_rows.append(
                {
                    "canonical_id": candidate.get("canonical_id", ""),
                    "heading": candidate.get("node", {}).get("heading", "") or candidate.get("heading", ""),
                    "jurisdiction": candidate.get("node", {}).get("jurisdiction", candidate.get("jurisdiction", "")),
                    "preview": (candidate.get("node", {}).get("text", "") or candidate.get("text", ""))[:240],
                    "fusion_score": candidate.get("fusion_score", 0.0),
                }
            )

        prompt = {
            "task": "Rerank tax-law retrieval candidates for a user query.",
            "query": query,
            "instructions": [
                "Return strict JSON only.",
                "Rank by legal relevance and specificity for the query.",
                "Output an array under key ranked with canonical_id and rerank_score between 0 and 1.",
            ],
            "candidates": compact_rows,
        }

        parsed = self.llm_client.complete_json(
            system_prompt="You are a legal retrieval reranker. Output JSON only.",
            user_prompt=json.dumps(prompt, ensure_ascii=False),
            temperature=0.0,
            timeout=45,
        )
        if not isinstance(parsed, dict):
            return []

        ranked = parsed.get("ranked", []) if isinstance(parsed, dict) else []
        out = []
        for item in ranked:
            cid = item.get("canonical_id")
            score = float(item.get("rerank_score", 0.0))
            if cid:
                out.append({"canonical_id": cid, "rerank_score": max(0.0, min(1.0, score))})
        return out

    def _is_provider_available(self) -> bool:
        provider = self.llm_client.config.provider
        if provider == "openai":
            return bool(self.api_key)
        if provider == "anthropic":
            return bool(os.getenv("ANTHROPIC_API_KEY"))
        if provider == "gemini":
            return bool(os.getenv("GOOGLE_API_KEY"))
        if provider == "llama_local":
            return True
        return False
