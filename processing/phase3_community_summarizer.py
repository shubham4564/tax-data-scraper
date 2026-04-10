"""Community summarization helpers for Phase 3 graph communities."""

from __future__ import annotations

from collections import Counter
from typing import Dict, List


class CommunitySummarizer:
    def __init__(self, llm_summarize=None):
        self.llm_summarize = llm_summarize

    def summarize(self, nodes: List[Dict]) -> str:
        if not nodes:
            return "No nodes available for summary."

        if self.llm_summarize is not None:
            try:
                llm_summary = self.llm_summarize(nodes)
                if llm_summary:
                    return llm_summary
            except Exception:
                pass

        headings = [node.get("heading", "").strip() for node in nodes if node.get("heading")]
        headings = [heading for heading in headings if heading]
        top_headings = [item[0] for item in Counter(headings).most_common(3)]
        lead_nodes = [self._short_label(node) for node in nodes[:5]]
        summary_parts = []
        if top_headings:
            summary_parts.append("Top headings: " + "; ".join(top_headings))
        if lead_nodes:
            summary_parts.append("Representative nodes: " + "; ".join(lead_nodes))
        return " | ".join(summary_parts)

    def _short_label(self, node: Dict) -> str:
        canonical_id = node.get("canonical_id", "")
        heading = node.get("heading", "")
        if heading:
            return f"{canonical_id}: {heading}"
        return canonical_id
