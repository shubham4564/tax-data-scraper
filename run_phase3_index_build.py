"""Phase 3 index build runner."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from processing.phase3_corpus_builder import Phase3CorpusBuilder
from processing.phase3_graph_index import Phase3GraphIndex
from processing.phase3_vector_index import DualVectorIndex


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Phase 3 graph and vector indexes.")
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    workspace_root = args.workspace_root
    output_dir = args.output_dir or (workspace_root / "data" / "processed" / "phase3")
    graph_dir = output_dir / "graph"
    vector_dir = output_dir / "vector"

    corpus_builder = Phase3CorpusBuilder(workspace_root=workspace_root, output_dir=output_dir)
    records, corpus_summary = corpus_builder.build()

    graph_index = Phase3GraphIndex(graph_dir)
    graph_summary = graph_index.build(records)

    vector_index = DualVectorIndex(vector_dir)
    vector_summary = vector_index.build(records)

    summary = {
        "corpus": corpus_summary,
        "graph": graph_summary,
        "vector": vector_summary,
    }
    with open(output_dir / "phase3_summary.json", "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
