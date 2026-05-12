import json
import requests
from typing import Dict, Any, List

class LLMEngine:
    def __init__(self):
        # Configuration provided in user prompt (Kalima OCR Qwen Endpoint)
        self.api_key = "sk-SsNrJQl7FaNMhtK1im0jvg"
        self.url = "https://qwen-api.kalima-ocr.com/chat/completions"
        self.model = "qwen-3.5-35b"

    def analyze_prescription(self, ocr_json: Dict[str, Any], ddi_context: str, language: str = 'fr') -> str:
        """
        Takes the extracted OCR data and the external databases context
        and prompts the LLM for a comprehensive clinical analysis.
        """

        lang_map = {'fr': 'French', 'en': 'English', 'ar': 'Arabic'}
        target_language = lang_map.get(language, 'French')

        prompt = f"""
You are an expert pharmacological consultant.
An OCR system has scanned a prescription, and drug-drug interactions (DDI) were queried from state-of-the-art pharmacological databases (OpenFDA, ANSM Thesaurus).

IMPORTANT: You MUST write your final response ENTIRELY in {target_language}.

=== EXTRACTED OCR DATA ===
{json.dumps(ocr_json, ensure_ascii=False, indent=2)}

=== EXTERNAL DDI DATABASE CONTEXT ===
{ddi_context}

Based on the above, please provide a clinical report containing:
1. Identified Drugs list
2. Drug-Drug Interactions (DDI) - strictly based on the external context.
3. Final recommendations or warnings.

Format your response in Markdown, but remember to translate ALL output into {target_language}.
"""

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": f"You are a clinical AI. Output strictly in {target_language}."},
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = requests.post(self.url, headers=headers, json=data, timeout=90)
            response.raise_for_status()
            res_json = response.json()
            return res_json['choices'][0]['message']['content']
        except Exception as e:
            return f"❌ Erreur lors de l'appel LLM: {str(e)}"

