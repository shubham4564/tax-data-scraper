"""Benchmark adapters for Phase 5 evaluation matrix."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def load_benchmark_samples(source: str, workspace_root: Path, benchmark_file: Path | None = None) -> List[Dict]:
    """Load and normalize benchmark samples into a common schema.

    Output schema per sample:
    - sample_id: str
    - query: str
    - jurisdiction: str | None
    - relevant_provisions: list[str]
    - expected_answer: str | None
    - benchmark_source: str
    """

    source_key = (source or "").strip().lower()

    if source_key == "proxy_scenarios":
        path = benchmark_file or (workspace_root / "data" / "processed" / "scenarios" / "scenarios.jsonl")
        return _load_proxy_scenarios(path)

    if source_key == "taxcalcbench":
        path = benchmark_file or (workspace_root / "data" / "raw" / "benchmark" / "taxcalcbench.jsonl")
        raise FileNotFoundError(
            f"TaxCalcBench file not found at {path}. Provide --benchmark-file with normalized JSONL to run this benchmark."
        )

    if source_key == "irs_vita":
        path = benchmark_file or (workspace_root / "data" / "raw" / "benchmark" / "irs_vita_questions.jsonl")
        raise FileNotFoundError(
            f"IRS VITA benchmark file not found at {path}. Provide --benchmark-file with normalized JSONL to run this benchmark."
        )

    raise ValueError(
        "Unsupported benchmark source. Use one of: proxy_scenarios, taxcalcbench, irs_vita"
    )


def _load_proxy_scenarios(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            raw = json.loads(line)
            rows.append(
                {
                    "sample_id": raw.get("scenario_id", ""),
                    "query": raw.get("query", ""),
                    "jurisdiction": raw.get("jurisdiction"),
                    "relevant_provisions": raw.get("relevant_provisions", []),
                    "expected_answer": raw.get("expected_answer"),
                    "benchmark_source": "proxy_scenarios",
                }
            )
    return rows
