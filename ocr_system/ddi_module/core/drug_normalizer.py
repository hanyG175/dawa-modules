from pathlib import Path
import json
import requests
import urllib.parse
import pandas as pd
from typing import Optional, Dict

class DrugNormalizer:
    def __init__(self):
        self.excel_path = Path(__file__).resolve().parents[1] / 'data' / 'algerian_meds.xlsx'
        self.nom_brand_to_dci_path = Path(__file__).resolve().parents[1] / 'data' / 'nomenclature_brand_to_dci.json'
        self.cleaned_inn_path = Path(__file__).resolve().parents[1] / 'data' / 'cleaned_inn.json'
        self.cleaned_inn_unique_path = Path(__file__).resolve().parents[1] / 'data' / 'cleaned_inn_unique.json'
        
        self.trade_to_dci = self._load_trade_to_dci()
        self.brand_to_inn = self._load_brand_to_inn()
        self.dci_to_inn = self._load_dci_to_inn()

    def _load_trade_to_dci(self) -> Dict[str, str]:
        mapping = {}
        if self.nom_brand_to_dci_path.exists():
            try:
                with open(self.nom_brand_to_dci_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        mapping[k.strip().lower()] = v.strip().lower()
            except Exception as e:
                print(f"Error loading nomenclature JSON: {e}")
        return mapping

    def _load_brand_to_inn(self) -> Dict[str, str]:
        mapping = {}
        if self.cleaned_inn_path.exists():
            try:
                with open(self.cleaned_inn_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        mapping[k.strip().lower()] = v.strip().lower()
            except Exception as e:
                print(f"Error loading INN JSON: {e}")
        return mapping

    def _load_dci_to_inn(self) -> Dict[str, str]:
        mapping = {}
        if self.cleaned_inn_unique_path.exists():
            try:
                with open(self.cleaned_inn_unique_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        mapping[k.strip().lower()] = v.strip().lower()
            except Exception as e:
                print(f"Error loading Unique DCI INN JSON: {e}")
        return mapping

    def translate_dci_to_inn(self, original_query: str, dci_french: str) -> str:
        """
        Translates a French DCI to an English INN.
        First tries to look up via the provided cleaned_inn map based on original query,
        then checks the DCI against the unique DCI mapping,
        then fallback to MyMemory Translation API or heuristics.
        """
        q_lower = original_query.strip().lower()
        if q_lower in self.brand_to_inn:
            return self.brand_to_inn[q_lower]
            
        d_lower = dci_french.strip().lower()
        if d_lower in self.dci_to_inn:
            return self.dci_to_inn[d_lower]

        try:
            url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(dci_french)}&langpair=fr|en"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("responseData") and data["responseData"].get("translatedText"):
                    return data["responseData"]["translatedText"].lower()
        except Exception:
            pass
            
        # Fallback heuristic (French DCI to English INN)
        dci = dci_french.lower()
        dci = dci.replace('é', 'e').replace('è', 'e')
        if dci.endswith('ine'):
            return dci[:-3] + 'in' # e.g. amoxicilline -> amoxicillin
        if dci.endswith('ol'):
            return dci # paracetamol stays paracetamol
        if "acide" in dci:
            return dci.replace("acide", "acid")
        
        return dci

    def normalize(self, query: str) -> dict:
        """
        Takes an OCR extracted name or manually entered TradeName/DCI.
        1. Checks DB for Trade Name to DCI.
        2. Translates to English INN using the cleaned map or fallback.
        """
        q_lower = query.strip().lower()
        dci_french = self.trade_to_dci.get(q_lower, query.strip())
        english_inn = self.translate_dci_to_inn(query, dci_french)
        
        return {
            "original_query": query,
            "dci_french": dci_french,
            "english_inn": english_inn
        }
