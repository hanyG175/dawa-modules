"""
42_generate_drug_notices.py
===========================
Generates individual drug notice documents (.txt) from the cleaned CSV data.

Each drug (clinical_profile_id) gets one notice per language, stored as:
    drug_notices/{language}/{cp_id}.txt

Each notice contains:
  - A metadata header with all universal market fields (aggregated across instances)
  - All non-empty clinical sections from the language's clinical_kb CSV

No special chunking delimiters are used — this is designed for
sentence-aware chunking with metadata enrichment in RAGFlow.
"""

import csv
import os
import re
import sys
from pathlib import Path
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")

# ────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────
BASE = Path(r"c:/Users/LENOVO/Code/PFE/data_cleaning")
SRC_DIR = BASE / "Data_Cleaned_NonRAG"
OUT_DIR = BASE / "drug_notices"
LANGUAGES = ["arabic", "english", "french"]

# Columns that are status/ID metadata (not clinical content)
SKIP_COLS = {
    "clinical_profile_id", "drugbank_id", "drugbank_name", "drugbank_status",
    "is_translated", "french_status", "arabic_status", "dci_arabic",
}

# ── ATC cleaning ───────────────────────────────────────────────────
ATC_CODE_PATTERN = re.compile(r'\b([A-Z]\d{2}[A-Z]{1,2}\d{1,2})\b', re.IGNORECASE)
NOISE_KEYWORDS = [
    "ordonnance", "remboursable", "pictogramme", "cliquant",
    "médicament", "indications thérapeutiques",
]


def clean_atc(atc_str: str) -> str:
    """Clean noisy ATC classification strings into a concise hierarchy."""
    if not atc_str or atc_str.strip().lower() in ("", "nan", "none"):
        return ""

    parts = [p.strip() for p in atc_str.split("|") if p.strip()]

    # If it looks like a clean pipe-separated hierarchy, keep it
    if (len(parts) > 1
            and all(len(p) < 80 for p in parts)
            and not any(any(kw in p.lower() for kw in NOISE_KEYWORDS) for p in parts)):
        return " | ".join(parts)

    # Extract ATC codes from noisy text
    found = ATC_CODE_PATTERN.findall(atc_str)
    if found:
        codes = sorted(set(c.upper() for c in found))
        return " | ".join(codes)

    # If the whole string is short and clean, keep it
    if len(atc_str) < 120 and not any(kw in atc_str.lower() for kw in NOISE_KEYWORDS):
        return atc_str.strip()

    return ""


# ── Data cleaning helpers ──────────────────────────────────────────
UNAVAILABLE = {"", "nan", "[data unavailable]", "none", "na", "n/a"}


def is_empty(val: str) -> bool:
    """Return True if a value is effectively missing / unavailable."""
    if val is None:
        return True
    s = str(val).strip()
    return s.lower() in UNAVAILABLE


def clean_text(val: str) -> str:
    """Light cleaning for clinical content fields."""
    if is_empty(val):
        return ""
    text = str(val).strip()
    # Collapse 3+ consecutive newlines into 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Strip trailing/leading whitespace per line
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text


def section_label(col_name: str) -> str:
    """Turn a column name into a readable section header."""
    col_name = re.sub(r'_(arabic|english|french)$', '', col_name, flags=re.IGNORECASE)
    return col_name.replace("_", " ").title()


# ────────────────────────────────────────────────────────────────────
# Load universal market data — aggregated per clinical_profile_id
# ────────────────────────────────────────────────────────────────────
def load_market_data(univ_path: Path) -> dict:
    """
    Returns a dict keyed by clinical_profile_id with aggregated market data:
        {
            "dci":              set of DCI names,
            "brand_names":      set of brand names,
            "forms":            set of pharmaceutical forms,
            "dosages":          set of dosages,
            "conditionnements": set of packaging descriptions,
            "laboratories":     set of laboratory names,
            "countries":        set of countries,
            "tarif_reference":  set of reference tariff values,
            "ppa":              set of PPA values,
            "liste_prescription": set of prescription list values,
            "atc":              set of cleaned ATC strings,
            "registration_numbers": set of registration numbers,
            "codes":            set of excel_codes,
        }
    """
    market = defaultdict(lambda: {
        "dci": set(), "brand_names": set(), "forms": set(),
        "dosages": set(), "conditionnements": set(), "laboratories": set(),
        "countries": set(), "tarif_reference": set(), "ppa": set(),
        "liste_prescription": set(), "atc": set(),
        "registration_numbers": set(), "codes": set(),
    })

    if not univ_path.exists():
        print(f"  WARNING: {univ_path} not found!")
        return dict(market)

    with univ_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cp_id = row.get("clinical_profile_id", "").strip()
            if not cp_id:
                continue

            m = market[cp_id]

            def _add(field_set, key):
                v = row.get(key, "").strip()
                if not is_empty(v):
                    field_set.add(v)

            _add(m["dci"], "dci")
            _add(m["brand_names"], "brand_name")
            _add(m["forms"], "form")
            _add(m["dosages"], "dosage")
            _add(m["conditionnements"], "conditionnement")
            _add(m["laboratories"], "laboratory")
            _add(m["countries"], "pays")
            _add(m["tarif_reference"], "tarif_reference_da")
            _add(m["ppa"], "ppa_da")
            _add(m["liste_prescription"], "liste_prescription")
            _add(m["registration_numbers"], "excel_n_enregistrement")
            _add(m["codes"], "excel_code")

            atc_raw = row.get("atc", "").strip()
            cleaned = clean_atc(atc_raw)
            if cleaned:
                m["atc"].add(cleaned)

    return dict(market)


# ────────────────────────────────────────────────────────────────────
# Build a single drug notice
# ────────────────────────────────────────────────────────────────────
def build_notice(cp_id: str, row: dict, lang: str, market: dict) -> str:
    """Compose a single drug notice from metadata + clinical sections."""
    m = market.get(cp_id)

    lines = []

    # ── Metadata header ───────────────────────────────────────────
    lines.append("=" * 60)
    lines.append("DRUG NOTICE")
    lines.append("=" * 60)
    lines.append("")

    # Drug Code
    lines.append(f"Drug Code: {cp_id}")

    # DCI / Active substance
    if lang == "arabic":
        dci_ar = row.get("dci_arabic", "").strip()
        if not is_empty(dci_ar):
            lines.append(f"DCI (Arabic): {dci_ar}")
    if m and m["dci"]:
        lines.append(f"DCI: {' | '.join(sorted(m['dci']))}")

    # DrugBank info (English only)
    if lang == "english":
        db_id = row.get("drugbank_id", "").strip()
        db_name = row.get("drugbank_name", "").strip()
        if not is_empty(db_id):
            lines.append(f"DrugBank ID: {db_id}")
        if not is_empty(db_name):
            lines.append(f"DrugBank Name: {db_name}")

    # Market metadata
    if m:
        if m["brand_names"]:
            lines.append(f"Brand Names: {' | '.join(sorted(m['brand_names']))}")
        if m["forms"]:
            lines.append(f"Pharmaceutical Forms: {' | '.join(sorted(m['forms']))}")
        if m["dosages"]:
            lines.append(f"Dosages: {' | '.join(sorted(m['dosages']))}")
        if m["conditionnements"]:
            lines.append(f"Packaging: {' | '.join(sorted(m['conditionnements']))}")
        if m["laboratories"]:
            lines.append(f"Laboratories: {' | '.join(sorted(m['laboratories']))}")
        if m["countries"]:
            lines.append(f"Countries: {' | '.join(sorted(m['countries']))}")
        if m["tarif_reference"]:
            lines.append(f"Reference Tariff (DA): {' | '.join(sorted(m['tarif_reference']))}")
        if m["ppa"]:
            lines.append(f"PPA (DA): {' | '.join(sorted(m['ppa']))}")
        if m["liste_prescription"]:
            lines.append(f"Prescription List: {' | '.join(sorted(m['liste_prescription']))}")
        if m["atc"]:
            lines.append(f"ATC Classification: {' | '.join(sorted(m['atc']))}")
        if m["registration_numbers"]:
            lines.append(f"Registration Numbers: {' | '.join(sorted(m['registration_numbers']))}")
        if m["codes"]:
            lines.append(f"Drug Codes: {' | '.join(sorted(m['codes']))}")

    lines.append("")
    lines.append("-" * 60)
    lines.append("")

    # ── Clinical sections ─────────────────────────────────────────
    section_count = 0
    for col, val in row.items():
        if col in SKIP_COLS:
            continue

        content = clean_text(val)
        if not content:
            continue

        label = section_label(col)
        lines.append(f"## {label}")
        lines.append("")
        lines.append(content)
        lines.append("")
        section_count += 1

    # Skip drug if there is literally no clinical data
    if section_count == 0:
        return ""

    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Main pipeline
# ────────────────────────────────────────────────────────────────────
def main():
    print("=" * 70)
    print("  Drug Notice Generator — Individual documents per drug per language")
    print("=" * 70)

    # Load market metadata
    univ_path = SRC_DIR / "universal_market_instances.csv"
    print(f"\nLoading market data from: {univ_path}")
    market = load_market_data(univ_path)
    print(f"  Loaded metadata for {len(market)} clinical profiles.")

    # Clean output directory
    if OUT_DIR.exists():
        import shutil
        print(f"\nCleaning output directory: {OUT_DIR}")
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    total_files = 0
    total_skipped = 0

    for lang in LANGUAGES:
        csv_path = SRC_DIR / f"clinical_kb_{lang}.csv"
        if not csv_path.exists():
            print(f"\n  WARNING: {csv_path} not found, skipping {lang}.")
            continue

        lang_dir = OUT_DIR / lang
        lang_dir.mkdir(parents=True, exist_ok=True)

        lang_files = 0
        lang_skipped = 0

        print(f"\nProcessing {lang.upper()}...")

        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cp_id = row.get("clinical_profile_id", "").strip()
                if not cp_id:
                    continue

                notice = build_notice(cp_id, row, lang, market)

                if not notice:
                    lang_skipped += 1
                    continue

                # Write individual file
                filename = f"{cp_id}.txt"
                out_path = lang_dir / filename
                with out_path.open("w", encoding="utf-8") as out_f:
                    out_f.write(notice)

                lang_files += 1

        print(f"  {lang.upper()}: {lang_files} notices written, {lang_skipped} skipped (no clinical data)")
        total_files += lang_files
        total_skipped += lang_skipped

    print(f"\n{'=' * 70}")
    print(f"  DONE — {total_files} total notices across {len(LANGUAGES)} languages")
    print(f"  Skipped: {total_skipped} (drugs with no clinical data in that language)")
    print(f"  Output: {OUT_DIR}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
