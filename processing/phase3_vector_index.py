"""Phase 3 dual vector index construction and retrieval."""

from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from processing.phase3_corpus_builder import CorpusRecord

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    faiss = None


@dataclass
class VectorSearchResult:
    canonical_id: str
    score: float
    content_score: float
    identifier_score: float
    metadata: Dict


class DualVectorIndex:
    def __init__(self, output_dir: Path, content_dim: int = 128, identifier_dim: int = 48):
        self.output_dir = output_dir
        self.content_dim = content_dim
        self.identifier_dim = identifier_dim
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._content_vectorizer: Optional[TfidfVectorizer] = None
        self._identifier_vectorizer: Optional[TfidfVectorizer] = None
        self._content_svd: Optional[TruncatedSVD] = None
        self._identifier_svd: Optional[TruncatedSVD] = None
        self._content_index = None
        self._identifier_index = None
        self._nodes: List[Dict] = []
        self._content_vectors: Optional[np.ndarray] = None
        self._identifier_vectors: Optional[np.ndarray] = None

    def build(self, records: List[CorpusRecord]) -> Dict:
        self._nodes = [self._record_to_row(record) for record in records]
        content_texts = [row["content_text"] or row["heading"] or row["canonical_id"] for row in self._nodes]
        identifier_texts = [row["identifier_text"] or row["canonical_id"] for row in self._nodes]

        content_matrix, identifier_matrix = self._fit_embeddings(content_texts, identifier_texts)
        self._content_vectors = self._prepare_dense(content_matrix, self.content_dim)
        self._identifier_vectors = self._prepare_dense(identifier_matrix, self.identifier_dim)

        self._content_index = self._build_ann_index(self._content_vectors)
        self._identifier_index = self._build_ann_index(self._identifier_vectors)
        self._persist()

        summary = {
            "total_nodes": len(self._nodes),
            "content_dim": int(self._content_vectors.shape[1]),
            "identifier_dim": int(self._identifier_vectors.shape[1]),
            "backend": "faiss" if faiss is not None else "numpy",
            "generated_at": datetime.now().isoformat(),
        }
        with open(self.output_dir / "vector_summary.json", "w", encoding="utf-8") as handle:
            json.dump(summary, handle, indent=2)
        return summary

    def search(
        self,
        query: str,
        k: int = 10,
        jurisdiction: Optional[str] = None,
        content_weight: float = 0.7,
        identifier_weight: float = 0.3,
    ) -> List[VectorSearchResult]:
        if self._content_vectors is None or self._identifier_vectors is None:
            self.load()

        content_query, identifier_query = self._encode_query(query)
        content_hits = self._search_index(self._content_index, self._content_vectors, content_query, k * 3)
        identifier_hits = self._search_index(self._identifier_index, self._identifier_vectors, identifier_query, k * 3)

        combined: Dict[str, Dict] = {}
        for idx, score in content_hits:
            node = self._nodes[idx]
            if jurisdiction and node["jurisdiction"] != jurisdiction:
                continue
            combined.setdefault(node["canonical_id"], self._blank_result(node))
            combined[node["canonical_id"]]["content_score"] = max(
                combined[node["canonical_id"]]["content_score"], float(score)
            )

        for idx, score in identifier_hits:
            node = self._nodes[idx]
            if jurisdiction and node["jurisdiction"] != jurisdiction:
                continue
            combined.setdefault(node["canonical_id"], self._blank_result(node))
            combined[node["canonical_id"]]["identifier_score"] = max(
                combined[node["canonical_id"]]["identifier_score"], float(score)
            )

        results: List[VectorSearchResult] = []
        for item in combined.values():
            score = content_weight * item["content_score"] + identifier_weight * item["identifier_score"]
            results.append(
                VectorSearchResult(
                    canonical_id=item["canonical_id"],
                    score=score,
                    content_score=item["content_score"],
                    identifier_score=item["identifier_score"],
                    metadata=item["metadata"],
                )
            )

        results.sort(key=lambda item: (-item.score, item.canonical_id))
        return results[:k]

    def load(self) -> None:
        self._nodes = self._read_jsonl(self.output_dir / "nodes.jsonl")
        with open(self.output_dir / "vector_artifacts.pkl", "rb") as handle:
            artifacts = pickle.load(handle)
        self._content_vectorizer = artifacts["content_vectorizer"]
        self._identifier_vectorizer = artifacts["identifier_vectorizer"]
        self._content_svd = artifacts["content_svd"]
        self._identifier_svd = artifacts["identifier_svd"]
        self._content_vectors = artifacts["content_vectors"]
        self._identifier_vectors = artifacts["identifier_vectors"]
        if faiss is not None and (self.output_dir / "content.faiss").exists():
            self._content_index = faiss.read_index(str(self.output_dir / "content.faiss"))
            self._identifier_index = faiss.read_index(str(self.output_dir / "identifier.faiss"))
        else:
            self._content_index = None
            self._identifier_index = None

    def _record_to_row(self, record: CorpusRecord) -> Dict:
        return {
            "canonical_id": record.canonical_id,
            "jurisdiction": record.jurisdiction,
            "node_type": record.node_type,
            "heading": record.heading,
            "text": record.text,
            "content_text": record.content_text,
            "identifier_text": record.identifier_text,
            "section_id": record.section_id,
            "node_path": record.node_path,
            "source_path": record.source_path,
            "metadata": record.metadata,
        }

    def _fit_embeddings(self, content_texts: List[str], identifier_texts: List[str]) -> Tuple[np.ndarray, np.ndarray]:
        self._content_vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=50000)
        self._identifier_vectorizer = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), max_features=20000)

        content_tfidf = self._content_vectorizer.fit_transform(content_texts)
        identifier_tfidf = self._identifier_vectorizer.fit_transform(identifier_texts)

        content_components = max(2, min(self.content_dim, content_tfidf.shape[1] - 1 if content_tfidf.shape[1] > 1 else 2))
        identifier_components = max(2, min(self.identifier_dim, identifier_tfidf.shape[1] - 1 if identifier_tfidf.shape[1] > 1 else 2))

        self._content_svd = TruncatedSVD(n_components=content_components, random_state=42)
        self._identifier_svd = TruncatedSVD(n_components=identifier_components, random_state=42)

        content_dense = self._content_svd.fit_transform(content_tfidf)
        identifier_dense = self._identifier_svd.fit_transform(identifier_tfidf)
        return content_dense, identifier_dense

    def _prepare_dense(self, matrix: np.ndarray, target_dim: int) -> np.ndarray:
        vectors = np.asarray(matrix, dtype=np.float32)
        if vectors.shape[1] < target_dim:
            padding = np.zeros((vectors.shape[0], target_dim - vectors.shape[1]), dtype=np.float32)
            vectors = np.hstack([vectors, padding])
        elif vectors.shape[1] > target_dim:
            vectors = vectors[:, :target_dim]
        return normalize(vectors, axis=1)

    def _build_ann_index(self, vectors: np.ndarray):
        if faiss is None:
            return None
        dim = vectors.shape[1]
        index = faiss.IndexHNSWFlat(dim, 32)
        index.hnsw.efConstruction = 40
        index.hnsw.efSearch = 64
        index.add(vectors.astype(np.float32))
        return index

    def _persist(self) -> None:
        self._write_jsonl(self.output_dir / "nodes.jsonl", self._nodes)
        with open(self.output_dir / "vector_artifacts.pkl", "wb") as handle:
            pickle.dump(
                {
                    "content_vectorizer": self._content_vectorizer,
                    "identifier_vectorizer": self._identifier_vectorizer,
                    "content_svd": self._content_svd,
                    "identifier_svd": self._identifier_svd,
                    "content_vectors": self._content_vectors,
                    "identifier_vectors": self._identifier_vectors,
                },
                handle,
            )
        if faiss is not None:
            faiss.write_index(self._content_index, str(self.output_dir / "content.faiss"))
            faiss.write_index(self._identifier_index, str(self.output_dir / "identifier.faiss"))

    def _encode_query(self, query: str) -> Tuple[np.ndarray, np.ndarray]:
        content = self._content_vectorizer.transform([query])
        identifier = self._identifier_vectorizer.transform([self._expand_query(query)])
        content_dense = self._prepare_dense(self._content_svd.transform(content), self._content_vectors.shape[1])
        identifier_dense = self._prepare_dense(self._identifier_svd.transform(identifier), self._identifier_vectors.shape[1])
        return content_dense.astype(np.float32), identifier_dense.astype(np.float32)

    def _search_index(self, index, vectors: np.ndarray, query_vector: np.ndarray, k: int) -> List[Tuple[int, float]]:
        if index is not None and faiss is not None:
            scores, indices = index.search(query_vector.astype(np.float32), k)
            pairs = []
            for idx, score in zip(indices[0].tolist(), scores[0].tolist()):
                if idx < 0:
                    continue
                pairs.append((idx, float(score)))
            return pairs

        scores = vectors @ query_vector.T
        score_list = scores.reshape(-1)
        top_indices = np.argsort(-score_list)[:k]
        return [(int(idx), float(score_list[idx])) for idx in top_indices]

    def _expand_query(self, query: str) -> str:
        tokens = []
        for token in query.split():
            cleaned = token.strip(".,:;()[]{}\"'`").lower()
            if cleaned:
                tokens.append(cleaned)
        return " ".join(tokens)

    def _blank_result(self, node: Dict) -> Dict:
        return {
            "canonical_id": node["canonical_id"],
            "content_score": 0.0,
            "identifier_score": 0.0,
            "metadata": node,
        }

    def _write_jsonl(self, path: Path, rows: List[Dict]) -> None:
        with open(path, "w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _read_jsonl(self, path: Path) -> List[Dict]:
        rows = []
        with open(path, "r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    rows.append(json.loads(line))
        return rows
