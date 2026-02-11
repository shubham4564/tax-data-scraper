"""
Evaluation metrics for legal tax IR system

Implements metrics for:
1. Retrieval evaluation (Recall@k, nDCG@k, MRR, no-miss rate)
2. Extraction evaluation (span F1, numeric accuracy, date correctness, attribution)
3. Reasoning evaluation (applicability, form/deadline accuracy, calibration)
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict
import json
from pathlib import Path
from scipy import stats


class RetrievalMetrics:
    """Metrics for document retrieval evaluation"""
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        Recall@k: fraction of relevant documents retrieved in top-k
        
        Args:
            retrieved: List of retrieved document IDs (ranked)
            relevant: List of relevant document IDs (gold standard)
            k: Cutoff position
        
        Returns:
            Recall@k score (0.0 to 1.0)
        """
        if not relevant:
            return 0.0
        
        retrieved_at_k = set(retrieved[:k])
        relevant_set = set(relevant)
        
        return len(retrieved_at_k & relevant_set) / len(relevant_set)
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """Precision@k"""
        if k == 0:
            return 0.0
        
        retrieved_at_k = set(retrieved[:k])
        relevant_set = set(relevant)
        
        return len(retrieved_at_k & relevant_set) / min(k, len(retrieved))
    
    @staticmethod
    def ndcg_at_k(retrieved: List[str], relevance_grades: Dict[str, int], k: int) -> float:
        """
        nDCG@k: Normalized Discounted Cumulative Gain
        
        Args:
            retrieved: List of retrieved document IDs (ranked)
            relevance_grades: Dict mapping doc_id -> grade (0-3)
            k: Cutoff position
        
        Returns:
            nDCG@k score (0.0 to 1.0)
        """
        # DCG@k
        dcg = 0.0
        for i, doc_id in enumerate(retrieved[:k]):
            rel = relevance_grades.get(doc_id, 0)
            dcg += (2**rel - 1) / np.log2(i + 2)  # i+2 because i is 0-indexed
        
        # Ideal DCG (IDCG)
        sorted_grades = sorted(relevance_grades.values(), reverse=True)
        idcg = 0.0
        for i, rel in enumerate(sorted_grades[:k]):
            idcg += (2**rel - 1) / np.log2(i + 2)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @staticmethod
    def mrr(retrieved_list: List[List[str]], relevant_list: List[str]) -> float:
        """
        Mean Reciprocal Rank
        
        Args:
            retrieved_list: List of ranked retrieval results (one per query)
            relevant_list: List of most relevant doc for each query
        
        Returns:
            MRR score
        """
        reciprocal_ranks = []
        
        for retrieved, most_relevant in zip(retrieved_list, relevant_list):
            try:
                rank = retrieved.index(most_relevant) + 1
                reciprocal_ranks.append(1.0 / rank)
            except ValueError:
                reciprocal_ranks.append(0.0)
        
        return np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    @staticmethod
    def no_miss_rate(retrieved_list: List[List[str]], 
                     mandatory_list: List[List[str]], 
                     k: int) -> float:
        """
        No-miss rate: fraction of queries where ALL mandatory docs are retrieved in top-k
        
        Args:
            retrieved_list: List of ranked retrieval results
            mandatory_list: List of mandatory doc sets (per query)
            k: Cutoff position
        
        Returns:
            No-miss rate (0.0 to 1.0)
        """
        no_misses = 0
        
        for retrieved, mandatory in zip(retrieved_list, mandatory_list):
            retrieved_at_k = set(retrieved[:k])
            mandatory_set = set(mandatory)
            
            if mandatory_set.issubset(retrieved_at_k):
                no_misses += 1
        
        return no_misses / len(retrieved_list) if retrieved_list else 0.0
    
    @staticmethod
    def compute_all_metrics(retrieved_list: List[List[str]],
                           gold_data: List[Dict],
                           k_values: List[int] = None) -> Dict:
        """
        Compute all retrieval metrics
        
        Args:
            retrieved_list: List of ranked retrieval results (one per scenario)
            gold_data: List of gold annotation dicts with:
                       - 'relevant': list of relevant doc IDs
                       - 'relevance_grades': dict of doc_id -> grade
                       - 'most_controlling': most important doc ID
                       - 'mandatory': list of mandatory doc IDs
            k_values: List of k values to evaluate (default: [5, 10, 50])
        
        Returns:
            Dict of metric_name -> score
        """
        if k_values is None:
            k_values = [5, 10, 50]
        
        metrics = {}
        
        # Recall@k for each k
        for k in k_values:
            recalls = [
                RetrievalMetrics.recall_at_k(retrieved, gold['relevant'], k)
                for retrieved, gold in zip(retrieved_list, gold_data)
            ]
            metrics[f'recall@{k}'] = np.mean(recalls)
            metrics[f'recall@{k}_std'] = np.std(recalls)
        
        # Precision@k
        for k in k_values:
            precisions = [
                RetrievalMetrics.precision_at_k(retrieved, gold['relevant'], k)
                for retrieved, gold in zip(retrieved_list, gold_data)
            ]
            metrics[f'precision@{k}'] = np.mean(precisions)
        
        # nDCG@k
        for k in k_values[:2]:  # Only for smaller k values
            ndcgs = [
                RetrievalMetrics.ndcg_at_k(retrieved, gold.get('relevance_grades', {}), k)
                for retrieved, gold in zip(retrieved_list, gold_data)
            ]
            metrics[f'ndcg@{k}'] = np.mean(ndcgs)
        
        # MRR
        most_controlling_list = [gold.get('most_controlling', gold['relevant'][0] if gold['relevant'] else None) 
                                  for gold in gold_data]
        metrics['mrr'] = RetrievalMetrics.mrr(retrieved_list, most_controlling_list)
        
        # No-miss rate
        mandatory_list = [gold.get('mandatory', gold['relevant']) for gold in gold_data]
        for k in k_values:
            metrics[f'no_miss_rate@{k}'] = RetrievalMetrics.no_miss_rate(
                retrieved_list, mandatory_list, k
            )
        
        return metrics


class ExtractionMetrics:
    """Metrics for information extraction evaluation"""
    
    @staticmethod
    def span_f1(pred_spans: List[Tuple[int, int]], 
                gold_spans: List[Tuple[int, int]]) -> Dict[str, float]:
        """
        Compute F1 for span matching
        
        Args:
            pred_spans: List of (start, end) tuples for predictions
            gold_spans: List of (start, end) tuples for gold
        
        Returns:
            Dict with precision, recall, f1
        """
        pred_set = set(pred_spans)
        gold_set = set(gold_spans)
        
        if not pred_set and not gold_set:
            return {'precision': 1.0, 'recall': 1.0, 'f1': 1.0}
        
        if not pred_set or not gold_set:
            return {'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
        
        tp = len(pred_set & gold_set)
        precision = tp / len(pred_set) if pred_set else 0.0
        recall = tp / len(gold_set) if gold_set else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        
        return {'precision': precision, 'recall': recall, 'f1': f1}
    
    @staticmethod
    def numeric_accuracy(pred_values: List[Dict], gold_values: List[Dict]) -> Dict[str, float]:
        """
        Evaluate numeric extraction accuracy
        
        Each value dict should have: {value, unit, period, scope}
        
        Returns:
            Dict with exact_match, value_accuracy, unit_accuracy
        """
        if not pred_values or not gold_values:
            return {'exact_match': 0.0, 'value_mae': float('inf'), 'unit_accuracy': 0.0}
        
        # Try to match predicted to gold (by position or context)
        exact_matches = 0
        value_errors = []
        unit_matches = 0
        
        # Simple matching: align by order (assumes same order)
        for pred, gold in zip(pred_values, gold_values):
            # Exact match
            if (pred['value'] == gold['value'] and 
                pred.get('unit') == gold.get('unit') and
                pred.get('period') == gold.get('period')):
                exact_matches += 1
            
            # Value error (with tolerance for rounding)
            value_error = abs(pred['value'] - gold['value'])
            value_errors.append(value_error)
            
            # Unit accuracy
            if pred.get('unit') == gold.get('unit'):
                unit_matches += 1
        
        n = min(len(pred_values), len(gold_values))
        
        return {
            'exact_match': exact_matches / n if n > 0 else 0.0,
            'value_mae': np.mean(value_errors) if value_errors else 0.0,
            'unit_accuracy': unit_matches / n if n > 0 else 0.0,
            'count_precision': n / len(pred_values) if pred_values else 0.0,
            'count_recall': n / len(gold_values) if gold_values else 0.0
        }
    
    @staticmethod
    def date_correctness(pred_dates: List[str], gold_dates: List[str]) -> Dict[str, float]:
        """
        Evaluate date extraction
        
        Args:
            pred_dates: List of date strings (ISO format)
            gold_dates: List of gold date strings
        
        Returns:
            Dict with exact_match and partial_match rates
        """
        if not pred_dates or not gold_dates:
            return {'exact_match': 0.0, 'partial_match': 0.0}
        
        exact = sum(1 for p, g in zip(pred_dates, gold_dates) if p == g)
        partial = sum(1 for p, g in zip(pred_dates, gold_dates) 
                     if p[:7] == g[:7])  # Year-month match
        
        n = min(len(pred_dates), len(gold_dates))
        
        return {
            'exact_match': exact / n if n > 0 else 0.0,
            'partial_match': partial / n if n > 0 else 0.0
        }
    
    @staticmethod
    def attribution_metrics(predictions: List[Dict], gold: List[Dict]) -> Dict[str, float]:
        """
        Evaluate evidence attribution
        
        Each dict should have: {field_value, evidence_span}
        
        Returns:
            Attribution precision and recall
        """
        # Attribution precision: % of predicted fields with correct evidence
        pred_with_evidence = sum(1 for p in predictions if p.get('evidence_span'))
        pred_correct_evidence = sum(
            1 for p, g in zip(predictions, gold)
            if p.get('evidence_span') == g.get('evidence_span')
        )
        
        attr_precision = (pred_correct_evidence / pred_with_evidence 
                         if pred_with_evidence > 0 else 0.0)
        
        # Attribution recall: % of gold fields with predicted evidence
        gold_with_evidence = sum(1 for g in gold if g.get('evidence_span'))
        attr_recall = (pred_correct_evidence / gold_with_evidence 
                      if gold_with_evidence > 0 else 0.0)
        
        return {
            'attribution_precision': attr_precision,
            'attribution_recall': attr_recall
        }


class ReasoningMetrics:
    """Metrics for reasoning/execution evaluation"""
    
    @staticmethod
    def applicability_accuracy(pred_jurisdictions: List[Set[str]],
                              gold_jurisdictions: List[Set[str]]) -> float:
        """
        Accuracy of jurisdiction/tax type applicability determination
        
        Returns:
            Fraction of scenarios with exact match
        """
        exact_matches = sum(1 for p, g in zip(pred_jurisdictions, gold_jurisdictions) if p == g)
        return exact_matches / len(pred_jurisdictions) if pred_jurisdictions else 0.0
    
    @staticmethod
    def form_accuracy(pred_forms: List[List[str]], gold_forms: List[List[str]]) -> Dict[str, float]:
        """
        Accuracy of required forms identification
        
        Returns:
            Precision, recall, F1 for form identification
        """
        precisions = []
        recalls = []
        
        for pred, gold in zip(pred_forms, gold_forms):
            pred_set = set(pred)
            gold_set = set(gold)
            
            if not pred_set and not gold_set:
                precisions.append(1.0)
                recalls.append(1.0)
                continue
            
            tp = len(pred_set & gold_set)
            p = tp / len(pred_set) if pred_set else 0.0
            r = tp / len(gold_set) if gold_set else 0.0
            
            precisions.append(p)
            recalls.append(r)
        
        avg_p = np.mean(precisions)
        avg_r = np.mean(recalls)
        f1 = 2 * avg_p * avg_r / (avg_p + avg_r) if (avg_p + avg_r) > 0 else 0.0
        
        return {'precision': avg_p, 'recall': avg_r, 'f1': f1}
    
    @staticmethod
    def brier_score(predicted_probs: List[float], outcomes: List[bool]) -> float:
        """
        Brier score for probability calibration
        
        Args:
            predicted_probs: List of predicted probabilities (0-1)
            outcomes: List of actual outcomes (True/False)
        
        Returns:
            Brier score (lower is better, 0 is perfect)
        """
        outcomes_numeric = [1.0 if o else 0.0 for o in outcomes]
        squared_errors = [(p - o)**2 for p, o in zip(predicted_probs, outcomes_numeric)]
        return np.mean(squared_errors)
    
    @staticmethod
    def expected_calibration_error(predicted_probs: List[float], 
                                   outcomes: List[bool], 
                                   n_bins: int = 10) -> float:
        """
        Expected Calibration Error (ECE)
        
        Args:
            predicted_probs: Predicted probabilities
            outcomes: Actual outcomes
            n_bins: Number of bins for calibration
        
        Returns:
            ECE score (lower is better)
        """
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        ece = 0.0
        outcomes_numeric = np.array([1.0 if o else 0.0 for o in outcomes])
        predicted_probs = np.array(predicted_probs)
        
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            # Find predictions in this bin
            in_bin = (predicted_probs >= bin_lower) & (predicted_probs < bin_upper)
            
            if in_bin.sum() == 0:
                continue
            
            # Average confidence in bin
            avg_confidence = predicted_probs[in_bin].mean()
            # Average accuracy in bin
            avg_accuracy = outcomes_numeric[in_bin].mean()
            # Weight by proportion in bin
            weight = in_bin.sum() / len(predicted_probs)
            
            ece += weight * abs(avg_confidence - avg_accuracy)
        
        return ece


class EvaluationRunner:
    """Run full evaluation pipeline"""
    
    def __init__(self, gold_file: str, predictions_file: str):
        self.gold_data = self._load_json(gold_file)
        self.predictions = self._load_json(predictions_file)
    
    def _load_json(self, filepath: str) -> Dict:
        """Load JSON or JSONL file"""
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        if filepath.endswith('.jsonl'):
            data = []
            with open(filepath, 'r') as f:
                for line in f:
                    data.append(json.loads(line))
            return data
        else:
            with open(filepath, 'r') as f:
                return json.load(f)
    
    def run_retrieval_eval(self, k_values: List[int] = None) -> Dict:
        """Run retrieval evaluation"""
        print("Running retrieval evaluation...")
        
        retrieved_list = [p['retrieved_docs'] for p in self.predictions]
        gold_list = [g for g in self.gold_data if 'relevant' in g]
        
        metrics = RetrievalMetrics.compute_all_metrics(retrieved_list, gold_list, k_values)
        
        return metrics
    
    def run_extraction_eval(self) -> Dict:
        """Run extraction evaluation"""
        print("Running extraction evaluation...")
        
        # This would need actual extraction predictions
        # Placeholder for structure
        metrics = {
            'condition_span_f1': 0.0,
            'numeric_exact_match': 0.0,
            'date_exact_match': 0.0,
            'attribution_precision': 0.0
        }
        
        return metrics
    
    def run_reasoning_eval(self) -> Dict:
        """Run reasoning evaluation"""
        print("Running reasoning evaluation...")
        
        metrics = {
            'applicability_accuracy': 0.0,
            'form_f1': 0.0,
            'brier_score': 0.0,
            'ece': 0.0
        }
        
        return metrics
    
    def generate_report(self, output_file: str = "evaluation_report.json"):
        """Generate comprehensive evaluation report"""
        report = {
            'evaluation_date': json.dumps(str(np.datetime64('now'))),
            'retrieval_metrics': self.run_retrieval_eval(),
            'extraction_metrics': self.run_extraction_eval(),
            'reasoning_metrics': self.run_reasoning_eval()
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nEvaluation report saved to: {output_file}")
        return report


def main():
    """Example usage"""
    print("=" * 60)
    print("Legal Tax IR Evaluation Metrics")
    print("=" * 60)
    print()
    
    # Example: Retrieval metrics
    print("Example: Computing retrieval metrics")
    print()
    
    retrieved_list = [
        ['doc1', 'doc2', 'doc3', 'doc4', 'doc5'],
        ['doc10', 'doc11', 'doc12']
    ]
    
    gold_data = [
        {
            'relevant': ['doc1', 'doc3', 'doc6'],
            'relevance_grades': {'doc1': 3, 'doc3': 2, 'doc6': 1},
            'most_controlling': 'doc1',
            'mandatory': ['doc1']
        },
        {
            'relevant': ['doc10', 'doc15'],
            'relevance_grades': {'doc10': 3, 'doc15': 2},
            'most_controlling': 'doc10',
            'mandatory': ['doc10', 'doc15']
        }
    ]
    
    metrics = RetrievalMetrics.compute_all_metrics(retrieved_list, gold_data, k_values=[3, 5, 10])
    
    print("Retrieval Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")
    
    print()
    print("Metrics implementation complete!")
    print("Use EvaluationRunner for full evaluation pipeline.")


if __name__ == "__main__":
    main()
