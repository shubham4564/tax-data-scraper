"""Phase 3 retrieval smoke test and evaluation runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from processing.phase3_retriever import Phase3Retriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 3 retrieval evaluation.")
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--phase3-dir", type=Path, default=None)
    parser.add_argument("--scenario-file", type=Path, default=None)
    parser.add_argument("--output-file", type=Path, default=None)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--jurisdiction", type=str, default=None)
    args = parser.parse_args()

    workspace_root = args.workspace_root
    phase3_dir = args.phase3_dir or (workspace_root / "data" / "processed" / "phase3")
    scenario_file = args.scenario_file or (workspace_root / "data" / "processed" / "scenarios" / "scenarios.jsonl")
    output_file = args.output_file or (phase3_dir / "retrieval_results.jsonl")

    retriever = Phase3Retriever(phase3_dir)

    rows = []
    with open(scenario_file, "r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            scenario = json.loads(line)
            query = scenario.get("query", "")
            jurisdiction = args.jurisdiction or scenario.get("jurisdiction")
            results = retriever.search(query=query, k=args.k, jurisdiction=jurisdiction)
            rows.append(
                {
                    "scenario_id": scenario.get("scenario_id"),
                    "query": query,
                    "jurisdiction": jurisdiction,
                    "results": results,
                }
            )

    with open(output_file, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(json.dumps({"queries_processed": len(rows), "output_file": str(output_file)}, indent=2))


if __name__ == "__main__":
    main()
