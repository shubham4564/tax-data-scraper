"""Phase 5 answer-correctness judge scaffold (LLM-as-judge)."""

from __future__ import annotations

import json
from typing import Dict, Optional

from processing.llm_provider_registry import LLMClient


class Phase5CorrectnessJudge:
    """Scores answer correctness on a 0-1 scale.

    This module is intentionally lightweight to enable matrix runs now.
    It can be integrated into the Phase 5 runner once gold answers/keys are available.
    """

    def __init__(self, judge_model: str = "gpt-5"):
        self.judge_model = judge_model
        self.client = LLMClient(judge_model)

    def score(
        self,
        *,
        query: str,
        answer: str,
        evidence_context: str,
        expected_answer: Optional[str] = None,
    ) -> Dict:
        rubric = {
            "task": "Score tax-answer correctness from 0 to 1.",
            "instructions": [
                "Use only provided question, answer, and optional expected answer/evidence.",
                "Penalize fabricated legal claims and unsupported conclusions.",
                "Return strict JSON with fields score (0-1), verdict, rationale.",
            ],
            "query": query,
            "answer": answer,
            "expected_answer": expected_answer,
            "evidence_context": evidence_context[:2500],
        }

        parsed = self.client.complete_json(
            system_prompt="You are an evaluation judge. Output JSON only.",
            user_prompt=json.dumps(rubric, ensure_ascii=False),
            temperature=0.0,
            timeout=45,
        )
        if not isinstance(parsed, dict):
            return {
                "score": None,
                "verdict": "unavailable",
                "rationale": "Judge model unavailable or response parse failure.",
                "judge_model": self.judge_model,
            }

        try:
            score = float(parsed.get("score", 0.0))
            score = max(0.0, min(1.0, score))
        except Exception:
            score = None

        return {
            "score": score,
            "verdict": str(parsed.get("verdict", "unknown")),
            "rationale": str(parsed.get("rationale", "")),
            "judge_model": self.judge_model,
        }
