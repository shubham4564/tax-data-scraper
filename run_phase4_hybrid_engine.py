"""Phase 4 hybrid retrieval + generation runner."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from processing.phase4_hybrid_retriever import Phase4HybridRetriever, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 4 hybrid retrieval engine.")
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--phase3-dir", type=Path, default=None)
    parser.add_argument("--scenario-file", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--model", type=str, default="gpt-4.1-mini")
    parser.add_argument("--k-vector", type=int, default=20)
    parser.add_argument("--k-graph", type=int, default=20)
    parser.add_argument("--k-final", type=int, default=10)
    parser.add_argument("--max-queries", type=int, default=None)
    args = parser.parse_args()

    workspace_root = args.workspace_root
    phase3_dir = args.phase3_dir or (workspace_root / "data" / "processed" / "phase3")
    scenario_file = args.scenario_file or (workspace_root / "data" / "processed" / "scenarios" / "scenarios.jsonl")
    output_dir = args.output_dir or (workspace_root / "data" / "processed" / "phase4")

    engine = Phase4HybridRetriever(phase3_dir=phase3_dir, model=args.model)

    outputs = []
    processed = 0
    with open(scenario_file, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            scenario = json.loads(line)
            query = scenario.get("query", "")
            jurisdiction = scenario.get("jurisdiction")

            result = engine.infer(
                query=query,
                jurisdiction=jurisdiction,
                k_vector=args.k_vector,
                k_graph=args.k_graph,
                k_final=args.k_final,
            )

            outputs.append(
                {
                    "scenario_id": scenario.get("scenario_id"),
                    "query": query,
                    "jurisdiction": jurisdiction,
                    "result": result,
                }
            )
            processed += 1
            if args.max_queries and processed >= args.max_queries:
                break

    output_path = output_dir / "generation_results.jsonl"
    write_jsonl(output_path, outputs)

    summary = {
        "queries_processed": processed,
        "output_file": str(output_path),
        "model": args.model,
        "generated_at": datetime.now().isoformat(),
    }
    (output_dir / "phase4_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
