"""Run Phase 5 controlled condition x model evaluation matrix."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import median
from typing import Dict, List

from evaluation.metrics import RetrievalMetrics
from evaluation.phase5_benchmark_adapters import load_benchmark_samples
from evaluation.phase5_correctness_judge import Phase5CorrectnessJudge
from processing.phase4_hybrid_retriever import write_jsonl
from processing.phase5_condition_runner import Phase5ConditionRunner


def _read_jsonl(path: Path) -> List[Dict]:
    rows: List[Dict] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _evaluate_rows(rows: List[Dict]) -> Dict:
    retrieved_list = []
    gold_data = []
    citation_valid = 0
    citations_total = 0

    timing_acc: Dict[str, List[float]] = defaultdict(list)

    for row in rows:
        result = row.get("result", {})
        merged = result.get("merged_candidates", [])
        generation = result.get("generation", {})
        timing = result.get("timing", {})

        retrieved_ids = [item.get("canonical_id") for item in merged if item.get("canonical_id")]
        retrieved_list.append(retrieved_ids)

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

        for key, value in timing.items():
            try:
                timing_acc[key].append(float(value))
            except Exception:
                continue

    retrieval_metrics = _safe_compute_retrieval_metrics(retrieved_list, gold_data) if rows else {}

    timing_summary = {}
    for key, values in timing_acc.items():
        if not values:
            continue
        ordered = sorted(values)
        timing_summary[key] = {
            "mean": sum(values) / len(values),
            "median": median(values),
            "p95": ordered[min(len(ordered) - 1, int(0.95 * (len(ordered) - 1)))],
        }

    return {
        "rows": len(rows),
        "retrieval_metrics": retrieval_metrics,
        "citation_accuracy": (citation_valid / citations_total) if citations_total else 0.0,
        "correctness": _aggregate_correctness(rows),
        "timing": timing_summary,
    }


def _aggregate_correctness(rows: List[Dict]) -> Dict:
    scores: List[float] = []
    unavailable = 0
    for row in rows:
        correctness = row.get("correctness", {})
        score = correctness.get("score") if isinstance(correctness, dict) else None
        if score is None:
            unavailable += 1
            continue
        try:
            scores.append(float(score))
        except Exception:
            unavailable += 1

    if not scores:
        return {
            "mean_score": None,
            "median_score": None,
            "available": 0,
            "unavailable": unavailable,
        }

    ordered = sorted(scores)
    return {
        "mean_score": sum(scores) / len(scores),
        "median_score": median(scores),
        "available": len(scores),
        "unavailable": unavailable,
        "p95": ordered[min(len(ordered) - 1, int(0.95 * (len(ordered) - 1)))],
    }


def _safe_compute_retrieval_metrics(retrieved_list: List[List[str]], gold_data: List[Dict]) -> Dict:
    try:
        return RetrievalMetrics.compute_all_metrics(retrieved_list, gold_data)
    except Exception:
        metrics: Dict[str, float] = {}
        k_values = [5, 10, 50]

        for k in k_values:
            recall_scores = []
            precision_scores = []
            no_miss = []

            for retrieved, gold in zip(retrieved_list, gold_data):
                relevant = set(gold.get("relevant", []))
                top_k = set((retrieved or [])[:k])
                denom_relevant = max(1, len(relevant))
                denom_precision = max(1, min(k, len(retrieved or [])))

                recall = len(top_k & relevant) / denom_relevant if relevant else 0.0
                precision = len(top_k & relevant) / denom_precision

                recall_scores.append(recall)
                precision_scores.append(precision)
                no_miss.append(1.0 if len(top_k & relevant) > 0 else 0.0)

            metrics[f"recall@{k}"] = sum(recall_scores) / max(1, len(recall_scores))
            metrics[f"precision@{k}"] = sum(precision_scores) / max(1, len(precision_scores))
            metrics[f"no_miss_rate@{k}"] = sum(no_miss) / max(1, len(no_miss))

        # Conservative fallbacks for metrics that require ranked graded relevance.
        metrics["ndcg@5"] = 0.0
        metrics["ndcg@10"] = 0.0
        metrics["mrr"] = 0.0
        return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 5 condition x model matrix evaluation.")
    parser.add_argument("--workspace-root", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--phase3-dir", type=Path, default=None)
    parser.add_argument("--scenario-file", type=Path, default=None)
    parser.add_argument("--benchmark-source", type=str, default="proxy_scenarios")
    parser.add_argument("--benchmark-file", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--models", type=str, default="gpt-5,claude-4.6-sonnet,llama-3.1,gemini-3")
    parser.add_argument("--conditions", type=str, default="baseline,vector_only,graph_only,hybrid")
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--k-vector", type=int, default=20)
    parser.add_argument("--k-graph", type=int, default=20)
    parser.add_argument("--k-final", type=int, default=10)
    parser.add_argument("--disable-llm-rerank", action="store_true")
    parser.add_argument("--enable-correctness-judge", action="store_true")
    parser.add_argument("--judge-model", type=str, default="gpt-5")
    parser.add_argument("--audit-sample-size", type=int, default=20)
    args = parser.parse_args()

    workspace_root = args.workspace_root
    phase3_dir = args.phase3_dir or (workspace_root / "data" / "processed" / "phase3")
    benchmark_file = args.benchmark_file or args.scenario_file
    output_dir = args.output_dir or (workspace_root / "data" / "processed" / "phase5")
    output_dir.mkdir(parents=True, exist_ok=True)

    scenarios = load_benchmark_samples(
        source=args.benchmark_source,
        workspace_root=workspace_root,
        benchmark_file=benchmark_file,
    )
    if args.max_queries:
        scenarios = scenarios[: args.max_queries]

    models = [item.strip() for item in args.models.split(",") if item.strip()]
    conditions = [item.strip() for item in args.conditions.split(",") if item.strip()]
    judge = Phase5CorrectnessJudge(judge_model=args.judge_model) if args.enable_correctness_judge else None

    matrix_summary = {
        "generated_at": datetime.now().isoformat(),
        "benchmark_source": args.benchmark_source,
        "benchmark_file": str(benchmark_file) if benchmark_file else None,
        "phase3_dir": str(phase3_dir),
        "models": models,
        "conditions": conditions,
        "rows_per_cell": len(scenarios),
        "correctness_judge_enabled": bool(judge),
        "correctness_judge_model": args.judge_model if judge else None,
        "cells": [],
    }

    for model in models:
        runner = Phase5ConditionRunner(phase3_dir=phase3_dir, model=model)

        for condition in conditions:
            rows: List[Dict] = []
            for scenario in scenarios:
                query = scenario.get("query", "")
                jurisdiction = scenario.get("jurisdiction")
                result = runner.run_query(
                    query=query,
                    jurisdiction=jurisdiction,
                    condition=condition,  # type: ignore[arg-type]
                    k_vector=args.k_vector,
                    k_graph=args.k_graph,
                    k_final=args.k_final,
                    enable_llm_rerank=not args.disable_llm_rerank,
                )

                correctness = None
                if judge is not None:
                    correctness = judge.score(
                        query=query,
                        answer=result.get("generation", {}).get("answer", ""),
                        evidence_context=result.get("context", {}).get("context_text", ""),
                        expected_answer=scenario.get("expected_answer"),
                    )

                rows.append(
                    {
                        "benchmark_source": scenario.get("benchmark_source", args.benchmark_source),
                        "sample_id": scenario.get("sample_id") or scenario.get("scenario_id"),
                        "query": query,
                        "jurisdiction": jurisdiction,
                        "relevant_provisions": scenario.get("relevant_provisions", []),
                        "expected_answer": scenario.get("expected_answer"),
                        "model": model,
                        "condition": condition,
                        "correctness": correctness,
                        "result": result,
                    }
                )

            cell_name = f"{condition}__{model}".replace("/", "_").replace(" ", "_")
            output_path = output_dir / f"phase5_results__{cell_name}.jsonl"
            write_jsonl(output_path, rows)

            eval_summary = _evaluate_rows(rows)
            cell_summary = {
                "model": model,
                "condition": condition,
                "output_file": str(output_path),
                "audit_sample": _build_audit_sample(rows, args.audit_sample_size),
                "evaluation": eval_summary,
            }
            matrix_summary["cells"].append(cell_summary)

    summary_path = output_dir / "phase5_matrix_summary.json"
    summary_path.write_text(json.dumps(matrix_summary, indent=2), encoding="utf-8")
    print(json.dumps({"output_dir": str(output_dir), "summary_file": str(summary_path), "cells": len(matrix_summary["cells"])}, indent=2))


def _build_audit_sample(rows: List[Dict], sample_size: int) -> List[Dict]:
    sample: List[Dict] = []
    for row in rows[: max(0, sample_size)]:
        sample.append(
            {
                "sample_id": row.get("sample_id"),
                "query": row.get("query"),
                "condition": row.get("condition"),
                "model": row.get("model"),
                "correctness": row.get("correctness"),
                "citations": row.get("result", {}).get("generation", {}).get("citations", []),
                "answer": row.get("result", {}).get("generation", {}).get("answer", ""),
            }
        )
    return sample


if __name__ == "__main__":
    main()
