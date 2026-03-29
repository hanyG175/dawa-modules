from flask import Flask, request, jsonify, render_template
import os
import sys
from pathlib import Path

# Add project root to sys path to find src module easily
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.engines.google_drive.service import GoogleDriveOCRModule
from src.core.parsing.french_medical_parser import FrenchDrugNoticeParser

app = Flask(__name__)
# Initialize OCR module and Parser
service = GoogleDriveOCRModule()
parser = FrenchDrugNoticeParser()

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/api/parse', methods=['POST'])
def parse_text():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'success': False, 'error': 'No text provided to parse'}), 400
        
    try:
        raw_text = data['text']
        parsed_obj = parser.parse(raw_text)
        parsed_dict = parsed_obj.to_dict()
        
        # Remove the massive raw cleaned text string to keep the JSON output clean
        if 'texte_brut_nettoye' in parsed_dict:
            del parsed_dict['texte_brut_nettoye']
            
        return jsonify({'success': True, 'data': parsed_dict})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask Web App...")
    print("Go to: http://127.0.0.1:5000 in your browser")
    app.run(host='127.0.0.1', port=5000, debug=True)
