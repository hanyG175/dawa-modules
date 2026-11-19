import re
import pandas as pd

INPUT_PATH = "final_clean_backups/clinical_kb_french.csv"
OUTPUT_BACKUP_PATH = "final_clean_backups/clinical_kb_french.csv"
OUTPUT_EXPORT_PATH = "Database_Exports/clinical_kb_french.csv"

FRENCH_COLS = [
    "indications",
    "posology",
    "contraindications",
    "precautions",
    "interactions",
    "pregnancy_breastfeeding",
    "mechanism_of_action",
    "adverse_effects",
    "conservation",
]

ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)


def fix_kerning(text: str) -> str:
    # Merge spaced letter sequences like "M e d i c a m e n t"
    return re.sub(r"\b(?:[A-Za-zÀ-ÖØ-öø-ÿ]\s+){2,}[A-Za-zÀ-ÖØ-öø-ÿ]\b", lambda m: m.group(0).replace(" ", ""), text)


def fix_apostrophes(text: str) -> str:
    text = text.replace("’", "'")
    text = re.sub(r"\b([ldjcntmqs])\s*'\s*", r"\1'", text, flags=re.IGNORECASE)
    text = re.sub(r"\bqu\s*'\s*", "qu'", text, flags=re.IGNORECASE)
    return text


def clean_french_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""

    text = URL_RE.sub("", text)
    text = fix_kerning(text)
    text = fix_apostrophes(text)

    # Remove Arabic lines if they slipped in
    lines = []
    for line in re.split(r"[\n\r]+", text):
        line = line.strip()
        if not line:
            continue
        if ARABIC_RE.search(line):
            continue
        lines.append(line)

    cleaned = " ".join(lines)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)

    return cleaned


def main():
    df = pd.read_csv(INPUT_PATH).fillna("")

    for col in FRENCH_COLS:
        if col in df.columns:
            df[col] = df[col].apply(clean_french_text)

    df.to_csv(OUTPUT_BACKUP_PATH, index=False)
    df.to_csv(OUTPUT_EXPORT_PATH, index=False)

    print("French dataset cleaned and updated in backups and Database_Exports.")


if __name__ == "__main__":
    main()
