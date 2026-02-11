"""
Retrieval Annotation Tool - Web Interface

Creates gold standard labels for document retrieval evaluation:
- Relevant sections per scenario
- Relevance grades (0-3)
- Most controlling section (for MRR)
- Mandatory sections (cannot miss)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify


class RetrievalAnnotator:
    """Manage retrieval annotation data"""
    
    def __init__(self, scenarios_file: str, statutes_dir: str, output_file: str):
        self.scenarios_file = Path(scenarios_file)
        self.statutes_dir = Path(statutes_dir)
        self.output_file = Path(output_file)
        
        self.scenarios = self._load_scenarios()
        self.annotations = self._load_existing_annotations()
        self.current_idx = 0
    
    def _load_scenarios(self) -> List[Dict]:
        """Load scenarios from JSONL file"""
        scenarios = []
        with open(self.scenarios_file, 'r') as f:
            for line in f:
                scenarios.append(json.loads(line))
        return scenarios
    
    def _load_existing_annotations(self) -> Dict:
        """Load existing annotations if available"""
        if self.output_file.exists():
            with open(self.output_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get_scenario(self, idx: int) -> Dict:
        """Get scenario by index"""
        return self.scenarios[idx] if idx < len(self.scenarios) else None
    
    def save_annotation(self, scenario_id: str, annotation: Dict):
        """Save retrieval annotation for a scenario"""
        annotation['annotated_date'] = datetime.now().isoformat()
        self.annotations[scenario_id] = annotation
        
        # Save to file
        with open(self.output_file, 'w') as f:
            json.dump(self.annotations, f, indent=2)
    
    def get_annotation(self, scenario_id: str) -> Optional[Dict]:
        """Get existing annotation for scenario"""
        return self.annotations.get(scenario_id)
    
    def get_progress(self) -> Dict:
        """Get annotation progress statistics"""
        return {
            'total_scenarios': len(self.scenarios),
            'annotated': len(self.annotations),
            'remaining': len(self.scenarios) - len(self.annotations),
            'percent_complete': (len(self.annotations) / len(self.scenarios) * 100) if self.scenarios else 0
        }


# Flask web interface for annotation
ANNOTATION_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Retrieval Annotation Tool</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; max-width: 1200px; }
        .header { background: #2c3e50; color: white; padding: 15px; margin-bottom: 20px; }
        .progress { background: #ecf0f1; padding: 10px; margin-bottom: 20px; }
        .scenario { background: #e8f4f8; padding: 15px; margin-bottom: 20px; border-left: 4px solid #3498db; }
        .section-item { background: #f9f9f9; padding: 10px; margin: 10px 0; border: 1px solid #ddd; }
        .controls { margin: 20px 0; }
        button { padding: 10px 20px; margin: 5px; cursor: pointer; }
        .btn-primary { background: #3498db; color: white; border: none; }
        .btn-success { background: #27ae60; color: white; border: none; }
        input[type="text"], textarea { width: 100%; padding: 8px; margin: 5px 0; }
        textarea { min-height: 100px; }
        .relevance-grade { margin: 10px 0; }
        .checkbox-group { margin: 10px 0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📋 Retrieval Annotation Tool</h1>
        <p>Create gold standard labels for document retrieval evaluation</p>
    </div>
    
    <div class="progress" id="progress">
        Loading progress...
    </div>
    
    <div class="scenario" id="scenario-display">
        <!-- Scenario will be loaded here -->
    </div>
    
    <div id="annotation-form" style="display:none;">
        <h3>Annotate Relevant Sections</h3>
        
        <div>
            <label><strong>Add Section:</strong></label>
            <input type="text" id="section-id" placeholder="Enter section number (e.g., 26-USC-61)">
            <input type="text" id="section-title" placeholder="Section title">
            <button onclick="addSection()" class="btn-primary">Add Section</button>
        </div>
        
        <h4>Relevant Sections:</h4>
        <div id="sections-list"></div>
        
        <div style="margin-top: 20px;">
            <label><strong>Most Controlling Section:</strong></label>
            <select id="most-controlling" style="width: 100%; padding: 8px;">
                <option value="">Select most controlling section</option>
            </select>
        </div>
        
        <div style="margin-top: 20px;">
            <label><strong>Notes:</strong></label>
            <textarea id="notes" placeholder="Any additional notes about this annotation..."></textarea>
        </div>
        
        <div class="controls">
            <button onclick="saveAnnotation()" class="btn-success">Save Annotation</button>
            <button onclick="skipScenario()" class="btn-primary">Skip</button>
            <button onclick="previousScenario()">← Previous</button>
            <button onclick="nextScenario()">Next →</button>
        </div>
    </div>
    
    <script>
        let currentIndex = 0;
        let currentScenario = null;
        let sections = [];
        
        async function loadProgress() {
            const response = await fetch('/api/progress');
            const data = await response.json();
            document.getElementById('progress').innerHTML = `
                <strong>Progress:</strong> ${data.annotated} / ${data.total_scenarios} scenarios annotated 
                (${data.percent_complete.toFixed(1)}% complete)
            `;
        }
        
        async function loadScenario(index) {
            const response = await fetch('/api/scenario/' + index);
            const data = await response.json();
            
            if (!data.scenario) {
                alert('No more scenarios!');
                return;
            }
            
            currentScenario = data.scenario;
            currentIndex = index;
            
            document.getElementById('scenario-display').innerHTML = `
                <h3>Scenario ${data.scenario.scenario_id}</h3>
                <p><strong>Jurisdiction:</strong> ${data.scenario.jurisdiction}</p>
                <p><strong>Tax Type:</strong> ${data.scenario.tax_type} - ${data.scenario.tax_subtype}</p>
                <p><strong>Tax Year:</strong> ${data.scenario.tax_year}</p>
                <p><strong>Complexity:</strong> ${data.scenario.complexity}</p>
                <hr>
                <h4>Query:</h4>
                <p style="font-size: 1.1em; font-style: italic;">${data.scenario.query}</p>
                <hr>
                <h4>Taxpayer Info:</h4>
                <pre>${JSON.stringify(data.scenario.taxpayer, null, 2)}</pre>
            `;
            
            // Load existing annotation if available
            if (data.annotation) {
                sections = data.annotation.sections || [];
                updateSectionsList();
            } else {
                sections = [];
                document.getElementById('sections-list').innerHTML = '<p>No sections added yet.</p>';
            }
            
            document.getElementById('annotation-form').style.display = 'block';
        }
        
        function addSection() {
            const sectionId = document.getElementById('section-id').value;
            const sectionTitle = document.getElementById('section-title').value;
            
            if (!sectionId) {
                alert('Please enter a section ID');
                return;
            }
            
            sections.push({
                section_id: sectionId,
                title: sectionTitle,
                relevance_grade: 1,
                is_mandatory: false
            });
            
            updateSectionsList();
            
            // Clear inputs
            document.getElementById('section-id').value = '';
            document.getElementById('section-title').value = '';
        }
        
        function removeSection(index) {
            sections.splice(index, 1);
            updateSectionsList();
        }
        
        function updateSectionsList() {
            const listDiv = document.getElementById('sections-list');
            const selectBox = document.getElementById('most-controlling');
            
            if (sections.length === 0) {
                listDiv.innerHTML = '<p>No sections added yet.</p>';
                selectBox.innerHTML = '<option value="">Select most controlling section</option>';
                return;
            }
            
            listDiv.innerHTML = sections.map((section, idx) => `
                <div class="section-item" id="section-${idx}">
                    <strong>${section.section_id}</strong> - ${section.title}
                    <div class="relevance-grade">
                        <label>Relevance Grade:</label>
                        <select onchange="updateRelevance(${idx}, this.value)">
                            <option value="1" ${section.relevance_grade === 1 ? 'selected' : ''}>1 - Marginally relevant</option>
                            <option value="2" ${section.relevance_grade === 2 ? 'selected' : ''}>2 - Relevant</option>
                            <option value="3" ${section.relevance_grade === 3 ? 'selected' : ''}>3 - Highly relevant</option>
                        </select>
                    </div>
                    <div class="checkbox-group">
                        <label>
                            <input type="checkbox" 
                                   ${section.is_mandatory ? 'checked' : ''} 
                                   onchange="updateMandatory(${idx}, this.checked)">
                            Mandatory (cannot miss)
                        </label>
                    </div>
                    <button onclick="removeSection(${idx})">Remove</button>
                </div>
            `).join('');
            
            // Update most controlling dropdown
            selectBox.innerHTML = `
                <option value="">Select most controlling section</option>
                ${sections.map(s => `<option value="${s.section_id}">${s.section_id}</option>`).join('')}
            `;
        }
        
        function updateRelevance(index, grade) {
            sections[index].relevance_grade = parseInt(grade);
        }
        
        function updateMandatory(index, isMandatory) {
            sections[index].is_mandatory = isMandatory;
        }
        
        async function saveAnnotation() {
            const mostControlling = document.getElementById('most-controlling').value;
            const notes = document.getElementById('notes').value;
            
            if (sections.length === 0) {
                alert('Please add at least one relevant section');
                return;
            }
            
            const annotation = {
                scenario_id: currentScenario.scenario_id,
                sections: sections,
                most_controlling_section: mostControlling,
                notes: notes
            };
            
            const response = await fetch('/api/annotate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(annotation)
            });
            
            if (response.ok) {
                alert('Annotation saved!');
                nextScenario();
            }
        }
        
        function nextScenario() {
            loadScenario(currentIndex + 1);
            loadProgress();
        }
        
        function previousScenario() {
            if (currentIndex > 0) {
                loadScenario(currentIndex - 1);
            }
        }
        
        function skipScenario() {
            nextScenario();
        }
        
        // Initialize
        loadProgress();
        loadScenario(0);
    </script>
</body>
</html>
'''


def create_annotation_app(scenarios_file: str, statutes_dir: str, output_file: str):
    """Create Flask application for annotation"""
    
    app = Flask(__name__)
    annotator = RetrievalAnnotator(scenarios_file, statutes_dir, output_file)
    
    @app.route('/')
    def index():
        return render_template_string(ANNOTATION_TEMPLATE)
    
    @app.route('/api/progress')
    def api_progress():
        return jsonify(annotator.get_progress())
    
    @app.route('/api/scenario/<int:index>')
    def api_scenario(index):
        scenario = annotator.get_scenario(index)
        if not scenario:
            return jsonify({'scenario': None})
        
        annotation = annotator.get_annotation(scenario['scenario_id'])
        return jsonify({
            'scenario': scenario,
            'annotation': annotation
        })
    
    @app.route('/api/annotate', methods=['POST'])
    def api_annotate():
        data = request.json
        annotator.save_annotation(data['scenario_id'], data)
        return jsonify({'success': True})
    
    return app


def main():
    """Run annotation tool"""
    print("=" * 60)
    print("Retrieval Annotation Tool")
    print("=" * 60)
    print()
    print("This tool helps create gold standard retrieval labels.")
    print("It will start a web interface on http://localhost:5000")
    print()
    
    scenarios_file = input("Scenarios file (default: data/processed/scenarios/scenarios.jsonl): ").strip()
    if not scenarios_file:
        scenarios_file = "data/processed/scenarios/scenarios.jsonl"
    
    statutes_dir = input("Statutes directory (default: data/raw): ").strip()  
    if not statutes_dir:
        statutes_dir = "data/raw"
    
    output_file = input("Output file (default: data/annotations/retrieval_gold.json): ").strip()
    if not output_file:
        output_file = "data/annotations/retrieval_gold.json"
    
    # Create output directory
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nStarting annotation server...")
    print(f"Open http://localhost:5000 in your browser")
    print(f"Annotations will be saved to: {output_file}")
    
    app = create_annotation_app(scenarios_file, statutes_dir, output_file)
    app.run(debug=True, port=5000)


if __name__ == "__main__":
    main()
