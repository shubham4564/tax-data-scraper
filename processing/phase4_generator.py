"""Answer generation with citations and out-of-scope gating for Phase 4."""

from __future__ import annotations

import json
import os
import re
from typing import Dict, List, Optional

from processing.llm_provider_registry import LLMClient


CITATION_RE = re.compile(r"\[CIT:([^\]]+)\]")


class Phase4Generator:
    def __init__(
        self,
        model: str = "gpt-4.1-mini",
        openai_api_key: Optional[str] = None,
        min_confidence: float = 0.20,
        min_citation_coverage: float = 0.50,
    ):
        self.model = model
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.min_confidence = min_confidence
        self.min_citation_coverage = min_citation_coverage
        self.llm_client = LLMClient(model)

    def generate(self, query: str, context_payload: Dict, ranked_candidates: List[Dict]) -> Dict:
        included_ids = context_payload.get("included_ids", [])
        context_text = context_payload.get("context_text", "")

        top_score = ranked_candidates[0].get("rerank_score", 0.0) if ranked_candidates else 0.0
        retrieval_confident = top_score >= self.min_confidence

        if not retrieval_confident or not included_ids:
            return self._out_of_scope_response(query, "Low retrieval confidence or empty context.")

        if self._can_use_remote_model():
            generated = self._openai_generate(query, context_text)
        else:
            generated = self._fallback_generate(query, ranked_candidates)

        cited_ids = self._extract_citations(generated.get("answer", ""))
        valid_citations = [cid for cid in cited_ids if cid in set(included_ids)]

        citation_coverage = len(valid_citations) / max(1, len(set(cited_ids)))
        strict_ok = retrieval_confident and citation_coverage >= self.min_citation_coverage

        if not strict_ok:
            return self._out_of_scope_response(
                query,
                "Insufficient grounded citations for strict policy.",
                retrieval_confidence=top_score,
                citation_coverage=citation_coverage,
            )

        generated.update(
            {
                "citations": valid_citations,
                "retrieval_confidence": top_score,
                "citation_coverage": citation_coverage,
                "out_of_scope": False,
            }
        )
        return generated

    def generate_baseline(self, query: str) -> Dict:
        """Generate an answer with no retrieval context for baseline condition."""
        system_prompt = "You are a tax assistant. Answer the query directly without retrieved legal context."
        user_prompt = json.dumps(
            {
                "task": "Provide a concise tax answer with uncertainty when needed.",
                "query": query,
                "output_schema": {"answer": "string", "confidence": "float_0_to_1"},
            },
            ensure_ascii=False,
        )

        if self._can_use_remote_model():
            parsed = self.llm_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                timeout=60,
            )
            if isinstance(parsed, dict):
                return {
                    "answer": str(parsed.get("answer", "")).strip() or "Insufficient information to answer confidently.",
                    "confidence": float(parsed.get("confidence", 0.0) or 0.0),
                    "out_of_scope": False,
                    "citations": [],
                    "retrieval_confidence": 0.0,
                    "citation_coverage": 0.0,
                }

        return {
            "answer": (
                "No-retrieval baseline response: unable to ground this answer in statutory context. "
                "Use retrieval-enabled modes for citation-backed outputs."
            ),
            "confidence": 0.2,
            "out_of_scope": False,
            "citations": [],
            "retrieval_confidence": 0.0,
            "citation_coverage": 0.0,
        }

    def _openai_generate(self, query: str, context_text: str) -> Dict:
        prompt = {
            "task": "Answer tax query using only provided context.",
            "requirements": [
                "Cite section IDs inline as [CIT:<canonical_id>] for every concrete legal claim.",
                "If context is insufficient, explicitly say so.",
            ],
            "query": query,
            "context": context_text,
            "output_schema": {
                "answer": "string",
                "confidence": "float_0_to_1",
            },
        }
        parsed = self.llm_client.complete_json(
            system_prompt="You are a tax-law assistant. Use only supplied context.",
            user_prompt=json.dumps(prompt, ensure_ascii=False),
            temperature=0.1,
            timeout=60,
        )
        if not isinstance(parsed, dict):
            return self._fallback_generate(query, [])
        try:
            return {
                "answer": str(parsed.get("answer", "")),
                "confidence": float(parsed.get("confidence", 0.0)),
            }
        except Exception:
            return self._fallback_generate(query, [])

    def _can_use_remote_model(self) -> bool:
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

    def _fallback_generate(self, query: str, ranked_candidates: List[Dict]) -> Dict:
        if not ranked_candidates:
            return {
                "answer": "The available legal context is insufficient for a grounded answer.",
                "confidence": 0.0,
            }

        top = ranked_candidates[:3]
        lines = [f"Query: {query}", "Grounded retrieval summary:"]
        for item in top:
            cid = item.get("canonical_id", "")
            heading = item.get("node", {}).get("heading", "") or item.get("heading", "")
            label = heading if heading else "Relevant statutory provision"
            lines.append(f"- {label} [CIT:{cid}]")

        lines.append("This response is retrieval-grounded and should be treated as informational, not legal advice.")
        return {
            "answer": "\n".join(lines),
            "confidence": min(0.85, max(0.35, top[0].get("rerank_score", top[0].get("fusion_score", 0.0)))),
        }

    def _extract_citations(self, answer_text: str) -> List[str]:
        return [item.strip() for item in CITATION_RE.findall(answer_text or "") if item.strip()]

    def _out_of_scope_response(
        self,
        query: str,
        reason: str,
        retrieval_confidence: float = 0.0,
        citation_coverage: float = 0.0,
    ) -> Dict:
        return {
            "answer": (
                "I cannot provide a grounded answer for this query with the current statutory context. "
                "Please refine the jurisdiction, tax type, or cite a target section."
            ),
            "confidence": 0.0,
            "out_of_scope": True,
            "reason": reason,
            "citations": [],
            "retrieval_confidence": retrieval_confidence,
            "citation_coverage": citation_coverage,
            "query": query,
        }
