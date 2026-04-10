"""Phase 4 evaluation runner for hybrid retrieval outputs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from evaluation.metrics import RetrievalMetrics


def _read_jsonl(path: Path) -> List[Dict]:
    rows = []
    if not path.exists():
        return rows
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate Phase 4 outputs.")
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--phase4-results", type=Path, default=None)
    parser.add_argument("--output-file", type=Path, default=None)
    args = parser.parse_args()

    workspace_root = args.workspace_root
    result_path = args.phase4_results or (workspace_root / "data" / "processed" / "phase4" / "generation_results.jsonl")
    output_file = args.output_file or (workspace_root / "data" / "processed" / "phase4" / "evaluation_summary.json")

    rows = _read_jsonl(result_path)

    retrieved_list = []
    gold_data = []
    citation_valid = 0
    citations_total = 0
    out_of_scope_count = 0

    for row in rows:
        result = row.get("result", {})
        generation = result.get("generation", {})
        merged = result.get("merged_candidates", [])

        retrieved_ids = [item.get("canonical_id") for item in merged if item.get("canonical_id")]
        retrieved_list.append(retrieved_ids)

        # Scenarios currently may not have relevant_provisions; keep evaluator robust.
        gold_relevant = row.get("relevant_provisions", [])
        gold_data.append(
            {
                "relevant": gold_relevant,
                "relevance_grades": {cid: 1 for cid in gold_relevant},
                "mandatory": gold_relevant,
            }
        )

        citations = generation.get("citations", [])
        context_ids = set(result.get("context", {}).get("included_ids", []))
        citations_total += len(citations)
        citation_valid += sum(1 for cid in citations if cid in context_ids)

        if generation.get("out_of_scope"):
            out_of_scope_count += 1

    retrieval_metrics = RetrievalMetrics.compute_all_metrics(retrieved_list, gold_data) if rows else {}
    citation_grounding_rate = (citation_valid / citations_total) if citations_total else 0.0

    summary = {
        "rows": len(rows),
        "retrieval_metrics": retrieval_metrics,
        "citation_grounding_rate": citation_grounding_rate,
        "out_of_scope_rate": (out_of_scope_count / len(rows)) if rows else 0.0,
        "generated_at": datetime.now().isoformat(),
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
