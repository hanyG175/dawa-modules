import json
from pathlib import Path
from typing import Dict, Any

from src.engines.google_drive.service import GoogleDriveOCRModule
from src.core.parsing.french_medical_parser import FrenchDrugNoticeParser

class MedicalOCRPipeline:
    """
    End-to-end processing pipeline that takes raw images/PDFs, 
    runs them through the OCR engine, and parses the extracted text 
    into structured JSON.
    """
    def __init__(self):
        # Initialize the underlying engine and parser logic independently
        self.ocr_engine = GoogleDriveOCRModule()
        self.parser = FrenchDrugNoticeParser()

    def process_file(self, file_path: str | Path, output_dir: str | Path) -> Dict[str, Any]:
        """Process a single file through OCR and Parsing, saving outputs to disk."""
        file_path = Path(file_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[{file_path.name}] Reading file...")
        with open(file_path, "rb") as f:
            payload = f.read()
            
        # 1. OCR Extraction (Using the existing robust module)
        print(f"[{file_path.name}] Running Google OCR...")
        ocr_result = self.ocr_engine.extract_from_bytes(file_path.name, payload)
        
        if not ocr_result.success:
            print(f"[{file_path.name}] ❌ OCR Failed: {ocr_result.error}")
            return {"success": False, "filename": file_path.name, "error": ocr_result.error}
            
        raw_text = ocr_result.text
        
        # 2. Save Raw OCR Backup
        raw_text_path = output_dir / f"{file_path.stem}_raw.txt"
        raw_text_path.write_text(raw_text, encoding="utf-8", errors="ignore")
        print(f"[{file_path.name}] ✅ Saved raw text -> {raw_text_path.name}")
        
        # 3. Medical Parsing
        print(f"[{file_path.name}] Parsing clinical fields...")
        parsed_data = self.parser.parse(raw_text)
        
        # 4. Save Structured JSON Data
        json_path = output_dir / f"{file_path.stem}_parsed.json"
        json_data = parsed_data.to_dict()
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print(f"[{file_path.name}] ✅ Saved parsed structures -> {json_path.name}")
        
        return {
            "success": True, 
            "filename": file_path.name,
            "raw_text_file": str(raw_text_path),
            "json_file": str(json_path),
            "data": json_data
        }
        
    def process_directory(self, input_dir: str | Path, output_dir: str | Path):
        """Batch process an entire directory of documents."""
        input_dir = Path(input_dir)
        valid_exts = {".pdf", ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
        
        results = []
        for file_path in input_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in valid_exts:
                res = self.process_file(file_path, output_dir)
                results.append(res)
                
        return results
