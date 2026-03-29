from flask import Flask, request, jsonify, render_template
import os
import sys
from pathlib import Path

# Add project root to sys path to find src module easily
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.engines.google_drive.service import GoogleDriveOCRModule

app = Flask(__name__)
# Keep the temp files logic exactly the same, this just hooks to the web UI
# Initialize OCR module
service = GoogleDriveOCRModule()

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

if __name__ == '__main__':
    print("Starting Flask Web App...")
    print("Go to: http://127.0.0.1:5000 in your browser")
    app.run(host='127.0.0.1', port=5000, debug=True)
