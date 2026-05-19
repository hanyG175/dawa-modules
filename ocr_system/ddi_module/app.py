from __future__ import annotations

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, render_template, redirect, url_for

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        pass


load_env_file(BASE_DIR / ".env")

from engines.google_drive.service import GoogleDriveOCRModule
from core.parsing import PrescriptionParser
from core.ddi_checker import DDIChecker
from core.llm_engine import LLMEngine
from core.drug_normalizer import DrugNormalizer

app = Flask(__name__, template_folder=str(BASE_DIR / "templates"))

ddi_checker = DDIChecker()
llm_engine = LLMEngine()
drug_normalizer = DrugNormalizer()
_ocr_service = None
_ocr_service_error = None


def get_ocr_service():
    global _ocr_service, _ocr_service_error
    if _ocr_service is not None:
        return _ocr_service
    if _ocr_service_error is not None:
        return None

    try:
        _ocr_service = GoogleDriveOCRModule()
        return _ocr_service
    except Exception as exc:
        _ocr_service_error = str(exc)
        return None

prescription_parser = PrescriptionParser()


@app.route("/")
def index():
    return redirect(url_for("ddi_analyzer"))


@app.route("/ddi")
def ddi_analyzer():
    return render_template("ddi_analyzer.html")


@app.route("/api/extract", methods=["POST"])
def extract():
    service = get_ocr_service()
    if service is None:
        return jsonify({
            "success": False,
            "error": _ocr_service_error or "OCR service is not configured. Add credentials/Google Drive auth files inside ddi_module/credentials.",
        }), 500

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "" or file.filename is None:
        return jsonify({"success": False, "error": "No selected file"}), 400

    try:
        payload = file.read()
        result = service.extract_from_bytes(file.filename, payload)
        return jsonify({
            "success": result.success,
            "file_name": result.file_name,
            "text": result.text,
            "characters": result.characters,
            "words": result.words,
            "error": result.error,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/manual_ddi", methods=["POST"])
def manual_ddi():
    data = request.get_json()
    if not data or "drugs" not in data:
        return jsonify({"success": False, "error": "No drugs provided"}), 400

    drugs = data["drugs"]
    target_lang = data.get("language", "fr")

    try:
        normalized_results = [drug_normalizer.normalize(d) for d in drugs]
        ddi_data = ddi_checker.fetch_all_context(normalized_results)
        ddi_context = ddi_data.get("text", "")
        ansm_pairs = ddi_data.get("ansm_pairs", [])

        pres_dict = {
            "medicaments_detectes": "\n".join(drugs),
            "normalization_context": normalized_results,
        }

        return jsonify({
            "success": True,
            "parsed_prescription": pres_dict,
            "ddi_context": ddi_context,
            "ansm_pairs": ansm_pairs,
            "llm_report": None,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/analyze_prescription", methods=["POST"])
def analyze_prescription_ddi():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"success": False, "error": "No text provided for analysis"}), 400

    raw_text = data["text"]
    target_lang = data.get("language", "fr")

    try:
        prescription_data = prescription_parser.parse(raw_text)
        pres_dict = prescription_data.to_dict()
    except Exception as e:
        return jsonify({"success": False, "error": f"Failed to parse prescription: {e}"}), 400

    d_list_raw = pres_dict.get("medicaments_detectes", "") or ""
    normalized_results = []

    for line in d_list_raw.split("\n"):
        words = line.split()
        if words and words[0].isalpha() and len(words[0]) > 3:
            raw_drug = words[0].lower()
            norm_info = drug_normalizer.normalize(raw_drug)
            normalized_results.append(norm_info)

    pres_dict["normalization_context"] = normalized_results

    try:
        if not normalized_results:
            normalized_results = [
                {"dci_french": "paracetamol", "english_inn": "paracetamol"},
                {"dci_french": "ibuprofene", "english_inn": "ibuprofen"},
            ]
        ddi_data = ddi_checker.fetch_all_context(normalized_results)
        ddi_context = ddi_data.get("text", "")
        ansm_pairs = ddi_data.get("ansm_pairs", [])
    except Exception as e:
        ddi_context = f"Erreur avec les bases de données externes: {e}"
        ansm_pairs = []

    return jsonify({
        "success": True,
        "parsed_prescription": pres_dict,
        "ddi_context": ddi_context,
        "ansm_pairs": ansm_pairs,
        "llm_report": None,
    })


@app.route("/api/generate_llm_report", methods=["POST"])
def generate_llm_report():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    pres_dict = data.get("parsed_prescription", {})
    ddi_context = data.get("ddi_context", "")
    target_lang = data.get("language", "fr")

    try:
        llm_analysis = llm_engine.analyze_prescription(pres_dict, ddi_context, language=target_lang)
        return jsonify({"success": True, "llm_report": llm_analysis})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/parse", methods=["POST"])
def parse_text():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"success": False, "error": "No text provided to parse"}), 400

    try:
        raw_text = data["text"]
        parsed_obj = prescription_parser.parse(raw_text)
        parsed_dict = parsed_obj.to_dict()
        if "texte_brut_nettoye" in parsed_dict:
            del parsed_dict["texte_brut_nettoye"]
        return jsonify({"success": True, "data": parsed_dict, "doc_type": "prescription"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("Starting standalone DDI module...")
    print("Go to: http://127.0.0.1:5000/ddi in your browser")
    app.run(host="127.0.0.1", port=5000, debug=True)
