"""
Extraction Annotation Tool

Creates gold standard labels for information extraction:
- Condition spans
- Exception spans
- Definition spans
- Numeric values (with units and ranges)
- Dates (effective dates, deadlines)
- Evidence spans (attribution)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class ExtractionAnnotator:
    """Manage extraction annotation data"""
    
    def __init__(self, sections_file: str, output_file: str):
        self.sections_file = Path(sections_file)
        self.output_file = Path(output_file)
        
        self.sections = self._load_sections()
        self.annotations = self._load_existing_annotations()
    
    def _load_sections(self) -> List[Dict]:
        """Load statute sections"""
        sections = []
        
        # Load from JSONL if available
        if self.sections_file.suffix == '.jsonl':
            with open(self.sections_file, 'r') as f:
                for line in f:
                    sections.append(json.loads(line))
        else:
            with open(self.sections_file, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    sections = data
                else:
                    sections = [data]
        
        return sections
    
    def _load_existing_annotations(self) -> Dict:
        """Load existing annotations"""
        if self.output_file.exists():
            with open(self.output_file, 'r') as f:
                return json.load(f)
        return {}
    
    def create_extraction_template(self, section_id: str, section_text: str) -> Dict:
        """Create template for extraction annotation"""
        return {
            'section_id': section_id,
            'section_text': section_text,
            'extractions': {
                'conditions': [
                    # {
                    #     'span_start': int,
                    #     'span_end': int,  
                    #     'text': str,
                    #     'condition_type': 'eligibility' | 'threshold' | 'requirement',
                    #     'evidence_span_start': int,
                    #     'evidence_span_end': int
                    # }
                ],
                'exceptions': [
                    # {
                    #     'span_start': int,
                    #     'span_end': int,
                    #     'text': str,
                    #     'exception_type': 'exclusion' | 'limitation' | 'special_case',
                    #     'evidence_span_start': int,
                    #     'evidence_span_end': int
                    # }
                ],
                'definitions': [
                    # {
                    #     'term': str,
                    #     'span_start': int,
                    #     'span_end': int,
                    #     'definition_text': str
                    # }
                ],
                'numeric_values': [
                    # {
                    #     'value': float,
                    #     'unit': 'dollar' | 'percent' | 'count',
                    #     'period': 'annual' | 'monthly' | 'one_time' | null,
                    #     'scope': 'individual' | 'joint' | 'corporate' | 'general',
                    #     'span_start': int,
                    #     'span_end': int,
                    #     'context': str,
                    #     'is_threshold': bool,
                    #     'evidence_span_start': int,
                    #     'evidence_span_end': int
                    # }
                ],
                'dates': [
                    # {
                    #     'date_type': 'effective_date' | 'deadline' | 'expiration',
                    #     'date_value': 'YYYY-MM-DD' | 'YYYY-MM' | 'YYYY',
                    #     'date_range_start': str,
                    #     'date_range_end': str,
                    #     'span_start': int,
                    #     'span_end': int,
                    #     'context': str
                    # }
                ],
                'forms_and_filings': [
                    # {
                    #     'form_number': str,
                    #     'form_name': str,
                    #     'requirement_type': 'mandatory' | 'conditional',
                    #     'span_start': int,
                    #     'span_end': int
                    # }
                ]
            },
            'metadata': {
                'annotator': '',
                'annotation_date': datetime.now().isoformat(),
                'time_spent_minutes': 0,
                'difficulty': '',  # 'easy' | 'medium' | 'hard'
                'notes': ''
            }
        }
    
    def save_annotation(self, section_id: str, annotation: Dict):
        """Save extraction annotation"""
        self.annotations[section_id] = annotation
        
        # Save to file
        with open(self.output_file, 'w') as f:
            json.dump(self.annotations, f, indent=2)
    
    def export_to_jsonl(self, output_path: str):
        """Export annotations to JSONL format (for training)"""
        with open(output_path, 'w') as f:
            for section_id, annotation in self.annotations.items():
                f.write(json.dumps({
                    'section_id': section_id,
                    **annotation
                }) + '\n')


def create_example_annotation():
    """Create an example annotation for reference"""
    
    example_section = """
    § 61. Gross income defined
    
    (a) General definition
    
    Except as otherwise provided in this subtitle, gross income means all income 
    from whatever source derived, including (but not limited to) the following items:
    
    (1) Compensation for services, including fees, commissions, fringe benefits, 
    and similar items;
    (2) Gross income derived from business;
    (3) Gains derived from dealings in property;
    (4) Interest;
    (5) Rents;
    (6) Royalties;
    (7) Dividends;
    (8) Annuities;
    (9) Income from life insurance and endowment contracts;
    (10) Pensions;
    (11) Income from discharge of indebtedness;
    (12) Distributive share of partnership gross income;
    (13) Income in respect of a decedent; and
    (14) Income from an interest in an estate or trust.
    """
    
    annotation = {
        'section_id': '26-USC-61',
        'section_text': example_section,
        'extractions': {
            'conditions': [
                {
                    'span_start': 52,
                    'span_end': 110,
                    'text': 'Except as otherwise provided in this subtitle',
                    'condition_type': 'exclusion',
                    'evidence_span_start': 52,
                    'evidence_span_end': 110
                }
            ],
            'definitions': [
                {
                    'term': 'gross income',
                    'span_start': 112,
                    'span_end': 170,
                    'definition_text': 'all income from whatever source derived'
                }
            ],
            'exceptions': [
                {
                    'span_start': 52,
                    'span_end': 98,
                    'text': 'otherwise provided in this subtitle',
                    'exception_type': 'exclusion',
                    'evidence_span_start': 52,
                    'evidence_span_end': 98
                }
            ],
            'numeric_values': [],
            'dates': [],
            'forms_and_filings': []
        },
        'metadata': {
            'annotator': 'example',
            'annotation_date': datetime.now().isoformat(),
            'time_spent_minutes': 15,
            'difficulty': 'easy',
            'notes': 'This is a definitional section with examples'
        }
    }
    
    return annotation


def create_annotation_guide():
    """Create annotation guidelines document"""
    
    guide = """
# Extraction Annotation Guidelines

## Overview
This guide explains how to annotate statutory text for information extraction evaluation.

## Annotation Types

### 1. Conditions
**What to annotate**: Text that specifies eligibility criteria, requirements, or thresholds.

**Types**:
- `eligibility`: Who qualifies (e.g., "individuals age 65 or older")
- `threshold`: Numeric conditions (e.g., "income exceeding $200,000")
- `requirement`: Mandatory conditions (e.g., "must file Form 1040")

**Example**:
"An individual with gross income exceeding $12,950 must file a return."
→ Annotate "with gross income exceeding $12,950" as condition (threshold)

### 2. Exceptions
**What to annotate**: Text that excludes cases or provides special treatment.

**Types**:
- `exclusion`: Explicitly excluded (e.g., "does not include gifts")
- `limitation`: Partial exclusion (e.g., "up to $10,000")
- `special_case`: Alternative treatment (e.g., "nonresidents follow different rules")

### 3. Definitions
**What to annotate**: Terms defined in the statute.

**Format**: Extract the term and its definition text.

### 4. Numeric Values
**What to annotate**: All numbers with tax relevance.

**Required fields**:
- `value`: The number (as float)
- `unit`: dollar, percent, count
- `period`: annual, monthly, one_time, or null
- `scope`: individual, joint, corporate, general
- `is_threshold`: true if this is a cutoff/threshold

**Example**:
"$12,950" → {value: 12950, unit: "dollar", period: "annual", scope: "individual"}

### 5. Dates
**What to annotate**: Effective dates, deadlines, expiration dates.

**Types**:
- `effective_date`: When a provision takes effect
- `deadline`: Filing or payment deadline
- `expiration`: When a provision expires

**Format**: Use ISO format (YYYY-MM-DD) when specific; YYYY or YYYY-MM when partial.

### 6. Forms and Filings
**What to annotate**: References to tax forms or filing requirements.

**Example**:
"must file Form 1040" → {form_number: "1040", form_name: "U.S. Individual Income Tax Return"}

## Evidence Spans
For conditions, exceptions, and numeric values, also annotate the **evidence span** - 
the text that supports this extraction.

Often the evidence span is the same as the extraction span, but sometimes it's broader context.

## Quality Guidelines

1. **Be precise**: Match exact text spans (character positions)
2. **Be complete**: Annotate ALL instances of each type
3. **Be consistent**: Use same annotation style throughout
4. **Context matters**: Include enough context to understand the extraction
5. **When in doubt**: Add a note explaining your decision

## Common Pitfalls

❌ **DON'T**: Paraphrase or summarize - extract exact text
❌ **DON'T**: Skip "obvious" extractions - annotate everything
❌ **DON'T**: Mix up span_start and span_end positions
✅ **DO**: Double-check character positions
✅ **DO**: Add notes for ambiguous cases
✅ **DO**: Track your time per section

## Example Workflow

1. Read the entire section first
2. Identify and mark all numeric values (easiest to spot)
3. Identify and mark all definitions
4. Identify conditions and exceptions
5. Identify dates and forms
6. Add evidence spans
7. Review: did you annotate everything?
8. Add metadata (difficulty, time, notes)

## Time Estimates
- Simple section (definitional): 10-15 minutes
- Moderate section (with conditions/numbers): 20-30 minutes  
- Complex section (many exceptions, tables): 40-60 minutes

## Questions?
If uncertain about an annotation, add a note and flag for review.
Aim for 80%+ inter-annotator agreement on clear cases.
"""
    
    return guide


def main():
    """Generate example annotation and guidelines"""
    
    print("=" * 60)
    print("Extraction Annotation Tool - Setup")
    print("=" * 60)
    print()
    
    # Create example
    example = create_example_annotation()
    example_file = Path("data/annotations/extraction_example.json")
    example_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(example_file, 'w') as f:
        json.dump(example, f, indent=2)
    print(f"✓ Created example annotation: {example_file}")
    
    # Create guidelines
    guide = create_annotation_guide()
    guide_file = Path("data/annotations/EXTRACTION_GUIDELINES.md")
    
    with open(guide_file, 'w') as f:
        f.write(guide)
    print(f"✓ Created annotation guidelines: {guide_file}")
    
    print()
    print("Next steps:")
    print("1. Review the example annotation")
    print("2. Read the annotation guidelines")
    print("3. Start annotating with a small pilot (5-10 sections)")
    print("4. Check inter-annotator agreement")
    print("5. Begin full annotation")
    print()
    print("MANUAL ANNOTATION PROCESS:")
    print("- Use a text editor or spreadsheet to annotate")
    print("- Or build a custom web interface (similar to retrieval_annotator.py)")
    print("- Follow the JSON schema in the example")
    print("- Save frequently!")


if __name__ == "__main__":
    main()
