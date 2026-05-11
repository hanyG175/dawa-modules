import re
import pandas as pd
from pyarabic import araby

INPUT_PATH = "final_clean_backups/clinical_kb_arabic.csv"
OUTPUT_BACKUP_PATH = "final_clean_backups/clinical_kb_arabic.csv"
OUTPUT_EXPORT_PATH = "Database_Exports/clinical_kb_arabic.csv"
OUTPUT_FOLDER = "Arabic_Cleaned_Output"
OUTPUT_CLEAN_CSV = f"{OUTPUT_FOLDER}/clinical_kb_arabic_cleaned.csv"
OUTPUT_RAG_TXT = f"{OUTPUT_FOLDER}/rag_arabic_cleaned.txt"

ARABIC_COLS = [
    "dci_arabic",
    "indications_arabic",
    "posology_arabic",
    "contraindications_arabic",
    "precautions_arabic",
    "interactions_arabic",
    "pregnancy_breastfeeding_arabic",
    "adverse_effects_arabic",
    "conservation_arabic",
    "mechanism_of_action_arabic",
]

NOISE_PHRASES = [
    "هل لديك اسئلة",
    "هل لديك أسئلة",
    "اسال سينا",
    "اسأل سينا",
    "اكتب سؤالك هنا",
    "انظر",
    "تعرف على كيفية",
    "قم بتحسين",
    "عرض عينة",
    "اطلع على البيانات",
    "Create Account",
    "Retrieved",
]

URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
ARABIC_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_RE = re.compile(r"[A-Za-z]")


def remove_kerning(text: str) -> str:
    # Only collapse spaced-out single-letter sequences, not normal word spacing.
    # Example: "م ؤ ل ل" -> "مؤلل" but "يستخدم علاج" stays intact.
    pattern = r"(?:(?<=^)|(?<=\s))([\u0600-\u06FF]\s+){2,}[\u0600-\u06FF]"
    return re.sub(pattern, lambda m: m.group(0).replace(" ", ""), text)


def normalize_arabic(text: str) -> str:
    text = araby.strip_tashkeel(text)
    text = araby.strip_tatweel(text)
    text = araby.normalize_hamza(text)
    return text


def clean_arabic_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""

    text = normalize_arabic(text)
    text = remove_kerning(text)

    # Remove URLs and obvious noise
    text = URL_RE.sub("", text)

    # Remove repeated characters (3+ -> 2)
    text = re.sub(r"([\u0600-\u06FF])\1{2,}", r"\1\1", text)

    # Remove mixed Latin noise blocks
    if LATIN_RE.search(text) and not ARABIC_RE.search(text):
        return ""

    # Remove known noise phrases line-by-line
    lines = []
    for line in re.split(r"[\n\r]+", text):
        line = line.strip()
        if not line:
            continue
        if any(p in line for p in NOISE_PHRASES):
            continue
        if URL_RE.search(line):
            continue
        # Drop lines that look like marketing/news
        if "انظر" in line and "الدواء" not in line:
            continue
        lines.append(line)

    if not lines:
        return ""

    cleaned = " ".join(lines)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Fix punctuation spacing
    cleaned = re.sub(r"\s+([،\.!؟])", r"\1", cleaned)

    return cleaned


def build_rag_block(row: dict) -> str:
    dci = row.get("dci_arabic") or "UNKNOWN DRUG"
    pid = row.get("clinical_profile_id", "UNKNOWN_ID")
    blocks = [f"=== DRUG: {dci} ===", f"ID: {pid}", ""]

    for col in ARABIC_COLS:
        if col not in row:
            continue
        val = clean_arabic_text(row.get(col, ""))
        if not val or len(val) < 15:
            continue
        field = col.replace("_arabic", "").replace("_", " ").upper()
        blocks.append(f"[ARABIC - {field}]")
        blocks.append(val)
        blocks.append("")

    if len(blocks) <= 3:
        return ""

    blocks.append("---")
    return "\n".join(blocks)


def main():
    df = pd.read_csv(INPUT_PATH).fillna("")

    # Clean Arabic columns
    for col in ARABIC_COLS:
        if col in df.columns:
            df[col] = df[col].apply(clean_arabic_text)

    # Save cleaned non-RAG version
    df.to_csv(OUTPUT_BACKUP_PATH, index=False)
    df.to_csv(OUTPUT_EXPORT_PATH, index=False)
    df.to_csv(OUTPUT_CLEAN_CSV, index=False)

    # Build RAG-formatted single file
    rag_blocks = []
    for _, row in df.iterrows():
        block = build_rag_block(row)
        if block:
            rag_blocks.append(block)

    with open(OUTPUT_RAG_TXT, "w", encoding="utf-8") as f:
        f.write("\n\n".join(rag_blocks))

    print(f"Saved cleaned Arabic CSV to: {OUTPUT_CLEAN_CSV}")
    print(f"Saved cleaned Arabic RAG text to: {OUTPUT_RAG_TXT}")


if __name__ == "__main__":
    main()
