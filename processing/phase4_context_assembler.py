"""Context assembly for Phase 4 generation."""

from __future__ import annotations

from typing import Dict, List, Set


class Phase4ContextAssembler:
    def __init__(self, max_words: int = 2200):
        self.max_words = max_words

    def assemble(self, ranked_candidates: List[Dict], broad_query: bool = False) -> Dict:
        blocks = []
        included_ids: List[str] = []
        words_used = 0
        seen: Set[str] = set()

        for item in ranked_candidates:
            canonical_id = item.get("canonical_id", "")
            if not canonical_id or canonical_id in seen:
                continue
            seen.add(canonical_id)

            node = item.get("node", {})
            heading = node.get("heading", "") or item.get("heading", "")
            text = node.get("text", "") or item.get("text", "")
            community_summary = item.get("community_summary", "") if broad_query else ""

            parts = [f"[SECTION] {canonical_id}"]
            if heading:
                parts.append(f"Heading: {heading}")
            if text:
                parts.append(f"Text: {text}")
            if community_summary:
                parts.append(f"Community Summary: {community_summary}")

            block = "\n".join(parts)
            block_words = len(block.split())
            if words_used + block_words > self.max_words:
                break

            blocks.append(block)
            included_ids.append(canonical_id)
            words_used += block_words

        context_text = "\n\n".join(blocks)
        return {
            "context_text": context_text,
            "included_ids": included_ids,
            "words_used": words_used,
            "truncated": len(included_ids) < len(seen),
        }
