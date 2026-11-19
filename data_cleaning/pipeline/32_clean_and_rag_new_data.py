import csv
import os
import re
from pathlib import Path
from collections import Counter

BASE = Path(r"c:\Users\LENOVO\Code\PFE\data_cleaning")
SRC_DIR = BASE / "new_data_dawav2_improved"
OUT_DIR = BASE / "new_data_rag"
BACKUP_DIR = SRC_DIR / "_backup_clean"  # backups of original CSVs

MAX_CHUNK_LEN = 8000
BATCH_SIZE = 500  # chunks per batch file


def normalize_header(h):
    if h is None:
        return ""
    return h.replace("\ufeff", "").strip()


def read_csv(path):
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = [normalize_header(h) for h in (reader.fieldnames or [])]
        rows = []
        for r in reader:
            row = {normalize_header(k): (v if v is not None else "") for k, v in r.items()}
            # ensure all headers exist
            for h in headers:
                row.setdefault(h, "")
            rows.append(row)
    return headers, rows


def write_csv(path, headers, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def dedupe_rows(headers, rows):
    row_tuples = [tuple(r.get(h, "") for h in headers) for r in rows]
    counts = Counter(row_tuples)
    seen = set()
    deduped = []
    for r, t in zip(rows, row_tuples):
        if t in seen:
            continue
        seen.add(t)
        deduped.append(r)
    dup_removed = sum(c - 1 for c in counts.values() if c > 1)
    return deduped, dup_removed


def drop_missing(rows, required_fields):
    kept = []
    dropped = 0
    for r in rows:
        if all((r.get(f, "").strip() != "") for f in required_fields):
            kept.append(r)
        else:
            dropped += 1
    return kept, dropped


def split_into_chunks(text, max_length=MAX_CHUNK_LEN):
    if not text:
        return []
    sentences = re.split(r"(?<=[.!?])\s+|\n", text)
    chunks = []
    current = ""
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(current) + len(s) + 1 <= max_length:
            current = f"{current}\n{s}" if current else s
        else:
            chunks.append(current)
            current = s
    if current:
        chunks.append(current)
    return chunks


def build_fields_text(row, headers, skip_fields=None):
    skip_fields = set(skip_fields or [])
    parts = []
    for h in headers:
        if h in skip_fields:
            continue
        v = str(row.get(h, "")).strip()
        if v:
            parts.append(v)
    return "\n".join(parts)


def write_rag_outputs(name, headers, rows, id_field=None, skip_fields=None, out_subdir=None):
    out_subdir = out_subdir or name
    out_dir = OUT_DIR / out_subdir
    out_dir.mkdir(parents=True, exist_ok=True)

    chunks = []
    for idx, r in enumerate(rows):
        entity = r.get(id_field, "") if id_field else ""
        if not entity:
            entity = f"{name}_{idx}"
        fields_text = build_fields_text(r, headers, skip_fields=skip_fields)
        if not fields_text.strip():
            continue
        for c_idx, c_text in enumerate(split_into_chunks(fields_text)):
            chunk_id = f"{entity.lower().replace(' ', '_')}_{name}_{c_idx}"
            content = f"[DRUG] {entity}\n\n{c_text}"
            chunks.append((chunk_id, content))

    global_path = out_dir / f"{name}_global.txt"
    with global_path.open("w", encoding="utf-8") as f:
        for chunk_id, content in chunks:
            f.write(f"[CHUNK_ID: {chunk_id}]\n")
            f.write(content)
            f.write("\n\n" + "=" * 80 + "\n\n")

    # batches
    if chunks:
        for i in range(0, len(chunks), BATCH_SIZE):
            batch_idx = i // BATCH_SIZE + 1
            batch_path = out_dir / f"{name}_batch_{batch_idx:03d}.txt"
            with batch_path.open("w", encoding="utf-8") as f:
                for chunk_id, content in chunks[i:i + BATCH_SIZE]:
                    f.write(f"[CHUNK_ID: {chunk_id}]\n")
                    f.write(content)
                    f.write("\n\n" + "=" * 80 + "\n\n")

    return len(chunks), global_path


def backup_original(path):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUP_DIR / path.name
    if not dest.exists():
        dest.write_bytes(path.read_bytes())


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = [
        ("clinical_kb_arabic", "clinical_kb_arabic.csv", "arabic", "clinical_profile_id", ["clinical_profile_id"]),
        ("clinical_kb_english", "clinical_kb_english.csv", "english", "clinical_profile_id", ["clinical_profile_id"]),
        ("clinical_kb_french", "clinical_kb_french.csv", "french", "clinical_profile_id", ["clinical_profile_id"]),
        ("universal_market_instances", "universal_market_instances.csv", "universal", "brand_name", ["instance_id", "clinical_profile_id", "brand_name", "dci"]),
    ]

    for name, filename, out_subdir, id_field, required_fields in targets:
        path = SRC_DIR / filename
        if not path.exists():
            print(f"Missing: {path}")
            continue

        backup_original(path)
        headers, rows = read_csv(path)

        # trim whitespace
        for r in rows:
            for h in headers:
                r[h] = str(r.get(h, "")).strip()

        # dedupe
        rows, dup_removed = dedupe_rows(headers, rows)

        # drop missing required fields (strict only for universal; for KBs, clinical_profile_id is required)
        rows, dropped_missing = drop_missing(rows, required_fields)

        # write cleaned csv back
        write_csv(path, headers, rows)

        print(f"{filename}: rows={len(rows)}, dup_removed={dup_removed}, dropped_missing={dropped_missing}")

        # RAG outputs
        skip_fields = []
        if name == "universal_market_instances":
            skip_fields = ["image_url", "detail_url"]
        chunk_count, global_path = write_rag_outputs(
            name=name,
            headers=headers,
            rows=rows,
            id_field=id_field,
            skip_fields=skip_fields,
            out_subdir=out_subdir,
        )
        print(f"  RAG chunks={chunk_count} -> {global_path}")


if __name__ == "__main__":
    main()
