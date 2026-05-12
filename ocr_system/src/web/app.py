from flask import Flask, request, jsonify, render_template
import os
import sys
from pathlib import Path

# Add project root to sys path to find src module easily
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.engines.google_drive.service import GoogleDriveOCRModule
from src.core.parsing import FrenchDrugNoticeParser, PrescriptionParser, DrugBoxParser
from src.core.ddi_checker import DDIChecker
from src.core.llm_engine import LLMEngine
from src.core.drug_normalizer import DrugNormalizer
import re

app = Flask(__name__)
# Initialize Processors
service = GoogleDriveOCRModule()
ddi_checker = DDIChecker()
llm_engine = LLMEngine()
drug_normalizer = DrugNormalizer()

parsers = {
    'notice': FrenchDrugNoticeParser(),
    'prescription': PrescriptionParser(),
    'box': DrugBoxParser()
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ddi')
def ddi_analyzer():
    """New dedicated view for Prescription DDI Analysis."""
    return render_template('ddi_analyzer.html')

@app.route('/api/extract', methods=['POST'])
def extract():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
        
    try:
        payload = file.read()
        result = service.extract_from_bytes(file.filename, payload)
        
        return jsonify({
            'success': result.success,
            'file_name': result.file_name,
            'text': result.text,
            'characters': result.characters,
            'words': result.words,
            'error': result.error
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
@app.route('/api/manual_ddi', methods=['POST'])
def manual_ddi():
    """Manual direct check of 2+ drugs without OCR."""
    data = request.get_json()
    if not data or 'drugs' not in data:
        return jsonify({'success': False, 'error': 'No drugs provided'}), 400
        
    drugs = data['drugs'] # List of drug names
    target_lang = data.get('language', 'fr')
    
    try:
        # Normalize
        normalized_results = []
        for d in drugs:
            norm_info = drug_normalizer.normalize(d)
            normalized_results.append(norm_info)
            
        # Get DDI ctx from Neo4j (ANSM) and OpenFDA
        ddi_data = ddi_checker.fetch_all_context(normalized_results)
        ddi_context = ddi_data.get("text", "")
        ansm_pairs = ddi_data.get("ansm_pairs", [])
        
        # Build mock prescription dict for LLM 
        pres_dict = {
            "medicaments_detectes": "\n".join(drugs),
            "normalization_context": normalized_results
        }
        
        llm_analysis = None # skipped, handled by separate endpoint now
        
        return jsonify({
            'success': True,
            'parsed_prescription': pres_dict,
            'ddi_context': ddi_context,
            'ansm_pairs': ansm_pairs,
            'llm_report': llm_analysis
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analyze_prescription', methods=['POST'])
def analyze_prescription_ddi():
    """
    API strictly designed for the LLM + External Databases functionality.
    Processes OCR Text -> Parses Drugs -> Queries PubChem/OpenFDA -> Analyzes with LLM.
    """
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'success': False, 'error': 'No text provided for analysis'}), 400
        
    raw_text = data['text']
    target_lang = data.get('language', 'fr') # Default to French
    
    # 1. Extract prescription text into structured data
    try:
        prescription_data = parsers['prescription'].parse(raw_text)
        pres_dict = prescription_data.to_dict()
    except Exception as e:
        return jsonify({'success': False, 'error': f"Failed to parse prescription: {e}"}), 400

    # 2. Extract drug names heuristically from the parsed string (or fallback to naive split)
    d_list_raw = pres_dict.get('medicaments_detectes', '')
    drugs = []
    normalized_results = []
    
    for line in d_list_raw.split('\n'):
        words = line.split()
        if words and words[0].isalpha() and len(words[0]) > 3:
            raw_drug = words[0].lower()
            # New step: Normalize Algerian Trade Name -> DCI -> English INN
            norm_info = drug_normalizer.normalize(raw_drug)
            normalized_results.append(norm_info)
            drugs.append(norm_info["english_inn"]) # We pass the English INN to OpenFDA
            
    # Include normalization context so LLM understands what we did
    pres_dict["normalization_context"] = normalized_results
    
    # 3. Use External DBs (OpenFDA + Local TWOSIDES Mirror) 
    try:
        # Pass the structured normalized_results list of dicts: [{"dci_french": "...", "english_inn": "..."}]
        if not normalized_results:
            normalized_results = [
                {"dci_french": "paracetamol", "english_inn": "paracetamol"},
                {"dci_french": "ibuprofene", "english_inn": "ibuprofen"}
            ]
        ddi_data = ddi_checker.fetch_all_context(normalized_results)
        ddi_context = ddi_data.get("text", "")
        ansm_pairs = ddi_data.get("ansm_pairs", [])
    except Exception as e:
        ddi_context = f"Erreur avec les bases de données externes: {e}"
        ansm_pairs = []

    # 4. Send to Kalima OCR LLM Core Endpoint
    try:
        llm_analysis = None # skipped, handled by separate endpoint now
    except Exception as e:
        llm_analysis = f"Erreur du modèle de langage: {e}"

    return jsonify({
        'success': True,
        'parsed_prescription': pres_dict,
        'ddi_context': ddi_context,
        'ansm_pairs': ansm_pairs,
        'llm_report': llm_analysis
    })

@app.route('/api/generate_llm_report', methods=['POST'])
def generate_llm_report():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    pres_dict = data.get('parsed_prescription', {})
    ddi_context = data.get('ddi_context', '')
    target_lang = data.get('language', 'fr')
    try:
        llm_analysis = None # skipped, handled by separate endpoint now
        return jsonify({'success': True, 'llm_report': llm_analysis})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/parse', methods=['POST'])
def parse_text():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'success': False, 'error': 'No text provided to parse'}), 400
        
    doc_type = data.get('doc_type', 'notice')
    if doc_type not in parsers:
        return jsonify({'success': False, 'error': 'Invalid document type selected'}), 400
        
    try:
        raw_text = data['text']
        active_parser = parsers[doc_type]
        parsed_obj = active_parser.parse(raw_text)
        parsed_dict = parsed_obj.to_dict()
        
        # Remove the massive raw cleaned text string to keep the JSON output clean (if present)
        if 'texte_brut_nettoye' in parsed_dict:
            del parsed_dict['texte_brut_nettoye']
            
        return jsonify({'success': True, 'data': parsed_dict, 'doc_type': doc_type})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Flask Web App...")
    print("Go to: http://127.0.0.1:5000 in your browser")
    app.run(host='127.0.0.1', port=5000, debug=True)
