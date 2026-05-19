"""
Coverage checker: Algerian brand → DCI map vs ANSM Neo4j graph.

Handles:
  - Salt/form suffixes:  ACEBUTOLOL CHLORHYDRATE  → acebutolol
  - Prefix forms:        ACETATE D'ABIRATERONE    → abiraterone
  - Combinations:        ASPIRINE/CAFEINE         → check each part separately
  - Fuzzy fallback for near-misses (accents, minor differences)

Reports at two levels:
  1. DCI level   — which unique DCI names are found/not found
  2. Brand level — how many brands have all / some / no DCIs covered

Requirements:
    pip install neo4j pandas rapidfuzz
"""

import re
import json
import pandas as pd
from neo4j import GraphDatabase
from rapidfuzz import process, fuzz

# ── Config — fill in your Aura credentials ───────────────────────────────────
NEO4J_URI      = "neo4j+s://6c51198a.databases.neo4j.io"   # your Aura URI
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "iG2wNnspn5U91akemAvUI_TZskhTEX5ZTNDwDionEk4"

JSON_PATH       = "data/nomenclature_brand_to_dci.json"
FUZZY_THRESHOLD = 88
# ─────────────────────────────────────────────────────────────────────────────

# Salt / form suffixes to strip (order matters — longest first)
SALT_SUFFIXES = [
    "dichlorhydrate", "chlorhydrate", "hydrochloride",
    "sodium", "potassium", "calcium", "magnesium", "zinc", "aluminium",
    "sulfate", "sulphate", "phosphate", "bisphosphate", "diphosphate",
    "acetate", "diacetate", "triacetate",
    "nitrate", "maleate", "fumarate", "tartrate", "hemitartrate",
    "mesylate", "mesilate", "besylate", "besilate", "tosylate",
    "succinate", "malate", "citrate", "gluconate", "lactate",
    "bromide", "bromhydrate", "iodide", "fluoride",
    "palmitate", "stearate", "valerate", "butyrate",
    "benzoate", "salicylate", "embonate", "pamoate",
    "trihydrate", "monohydrate", "anhydre", "anhydrous",
    "hemifumarate", "hemihydrate", "monosodique", "disodique",
    "tert-butylamine", "trometamol", "meglumine",
]

# Prefix forms to strip:  "ACETATE DE X" → X,  "CHLORURE DE X" → X
PREFIX_PATTERNS = [
    r"^acétate\s+d[e'][\s']+",
    r"^acetate\s+d[e'][\s']+",
    r"^acétate\s+de\s+",
    r"^acetate\s+de\s+",
    r"^chlorure\s+de\s+",
    r"^sulfate\s+de\s+",
    r"^phosphate\s+de\s+",
    r"^gluconate\s+de\s+",
    r"^succinate\s+de\s+",
    r"^malate\s+de\s+",
    r"^citrate\s+de\s+",
    r"^tartrate\s+de\s+",
    r"^maleate\s+de\s+",
    r"^fumarate\s+de\s+",
    r"^bromhydrate\s+de\s+",
    r"^mesylate\s+de\s+",
    r"^nitrate\s+de\s+",
    r"^benzoate\s+de\s+",
    r"^palmitate\s+de\s+",
    r"^valerate\s+de\s+",
    r"^dipropionate\s+de\s+",
    r"^propionate\s+de\s+",
    r"^undécylénate\s+de\s+",
    r"^undecylenate\s+de\s+",
    r"^embonate\s+de\s+",
]

COMBO_SEPARATORS = re.compile(r"\s*/\s*|\s+ET\s+", re.IGNORECASE)


def normalise(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"-\s+", "-", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s


def strip_salt(name: str) -> str:
    """Remove trailing salt/form suffix from a normalised DCI name."""
    for suffix in SALT_SUFFIXES:
        pattern = r"\s+" + re.escape(suffix) + r"(\s+.*)?$"
        stripped = re.sub(pattern, "", name).strip()
        if stripped != name:
            return stripped
    return name


def strip_prefix(name: str) -> str:
    """Remove leading 'FORME DE ' prefix from a normalised DCI name."""
    for pat in PREFIX_PATTERNS:
        stripped = re.sub(pat, "", name, flags=re.IGNORECASE).strip()
        if stripped != name:
            return stripped
    return name


def split_combination(dci: str) -> list[str]:
    """Split a combination DCI into its individual components."""
    parts = COMBO_SEPARATORS.split(dci)
    return [p.strip() for p in parts if p.strip()]


def candidate_forms(raw_dci: str) -> list[str]:
    """
    Generate all lookup candidates for a raw DCI string, from most to least specific:
      1. normalised as-is
      2. salt stripped
      3. prefix stripped
      4. both prefix and salt stripped
    """
    n = normalise(raw_dci)
    candidates = [n]
    s = strip_salt(n)
    if s != n:
        candidates.append(s)
    p = strip_prefix(n)
    if p != n:
        candidates.append(p)
        ps = strip_salt(p)
        if ps != p:
            candidates.append(ps)
    return candidates


# ── Neo4j ─────────────────────────────────────────────────────────────────────

def load_graph_names(driver) -> dict[str, dict]:
    query = """
    MATCH (n) WHERE n:Substance OR n:Class
    RETURN
      CASE WHEN n:Substance THEN n.substanceId ELSE n.classId END AS id,
      n.name AS name,
      labels(n)[0] AS label
    """
    graph = {}
    with driver.session() as session:
        for rec in session.run(query):
            graph[normalise(rec["name"])] = {
                "id": rec["id"], "name": rec["name"], "label": rec["label"]
            }
    return graph


# ── Matching ──────────────────────────────────────────────────────────────────

def match_single_dci(raw_dci: str, graph: dict, graph_keys: list,
                     threshold: int) -> dict:
    """Try to match one DCI component against the graph."""
    for candidate in candidate_forms(raw_dci):
        if candidate in graph:
            return {
                "dci_raw":     raw_dci,
                "matched_to":  graph[candidate]["name"],
                "label":       graph[candidate]["label"],
                "graph_id":    graph[candidate]["id"],
                "match_type":  "exact",
                "score":       100,
                "candidate":   candidate,
            }

    # Fuzzy on all candidates
    best_result = None
    best_score  = 0
    for candidate in candidate_forms(raw_dci):
        hit = process.extractOne(
            candidate, graph_keys,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
        )
        if hit and hit[1] > best_score:
            best_score  = hit[1]
            best_result = hit

    if best_result:
        matched_norm, score, _ = best_result
        return {
            "dci_raw":    raw_dci,
            "matched_to": graph[matched_norm]["name"],
            "label":      graph[matched_norm]["label"],
            "graph_id":   graph[matched_norm]["id"],
            "match_type": "fuzzy",
            "score":      score,
            "candidate":  normalise(raw_dci),
        }

    return {
        "dci_raw":    raw_dci,
        "matched_to": None,
        "label":      None,
        "graph_id":   None,
        "match_type": "no_match",
        "score":      0,
        "candidate":  normalise(raw_dci),
    }


def check_coverage(brand_map: dict, graph: dict, threshold: int):
    graph_keys = list(graph.keys())

    # ── DCI-level results ─────────────────────────────────────────────────────
    unique_dcis = set(brand_map.values())
    dci_results: dict[str, dict] = {}

    for raw_dci in sorted(unique_dcis):
        parts = split_combination(raw_dci)
        if len(parts) == 1:
            dci_results[raw_dci] = match_single_dci(raw_dci, graph, graph_keys, threshold)
        else:
            # Combination: match each part independently
            part_matches = [match_single_dci(p, graph, graph_keys, threshold) for p in parts]
            found   = [m for m in part_matches if m["match_type"] != "no_match"]
            missing = [m for m in part_matches if m["match_type"] == "no_match"]
            if len(found) == len(parts):
                status = "exact" if all(m["match_type"] == "exact" for m in found) else "fuzzy"
            elif found:
                status = "partial"
            else:
                status = "no_match"
            dci_results[raw_dci] = {
                "dci_raw":       raw_dci,
                "is_combination": True,
                "n_parts":       len(parts),
                "n_found":       len(found),
                "match_type":    status,
                "parts":         part_matches,
                "matched_to":    " + ".join(m["matched_to"] or "?" for m in part_matches),
                "score":         min((m["score"] for m in part_matches), default=0),
            }

    # ── Brand-level results ───────────────────────────────────────────────────
    brand_rows = []
    for brand, raw_dci in brand_map.items():
        r = dci_results[raw_dci]
        brand_rows.append({
            "brand":      brand,
            "dci":        raw_dci,
            "match_type": r["match_type"],
            "matched_to": r.get("matched_to"),
            "score":      r.get("score", 0),
        })

    return dci_results, brand_rows


# ── Reporting ─────────────────────────────────────────────────────────────────

def print_report(dci_results: dict, brand_rows: list):
    total_dci   = len(dci_results)
    exact_dci   = sum(1 for r in dci_results.values() if r["match_type"] == "exact")
    fuzzy_dci   = sum(1 for r in dci_results.values() if r["match_type"] == "fuzzy")
    partial_dci = sum(1 for r in dci_results.values() if r["match_type"] == "partial")
    none_dci    = sum(1 for r in dci_results.values() if r["match_type"] == "no_match")

    total_brand   = len(brand_rows)
    exact_brand   = sum(1 for r in brand_rows if r["match_type"] == "exact")
    fuzzy_brand   = sum(1 for r in brand_rows if r["match_type"] == "fuzzy")
    partial_brand = sum(1 for r in brand_rows if r["match_type"] == "partial")
    none_brand    = sum(1 for r in brand_rows if r["match_type"] == "no_match")
    covered_brand = exact_brand + fuzzy_brand + partial_brand

    print("=" * 68)
    print("  ANSM Graph Coverage — Algerian Brand→DCI Map")
    print("=" * 68)
    print(f"\n  ── DCI level ({total_dci} unique DCIs) ──────────────────────────")
    print(f"  Exact match          : {exact_dci:4d}  ({exact_dci/total_dci*100:.1f}%)")
    print(f"  Fuzzy match          : {fuzzy_dci:4d}  ({fuzzy_dci/total_dci*100:.1f}%)")
    print(f"  Partial (combo)      : {partial_dci:4d}  ({partial_dci/total_dci*100:.1f}%)")
    print(f"  Not found            : {none_dci:4d}  ({none_dci/total_dci*100:.1f}%)")
    print(f"  ── Coverage          : {(total_dci-none_dci)/total_dci*100:.1f}%")

    print(f"\n  ── Brand level ({total_brand} brands) ──────────────────────────")
    print(f"  Fully covered        : {exact_brand+fuzzy_brand:4d}  ({(exact_brand+fuzzy_brand)/total_brand*100:.1f}%)")
    print(f"  Partially covered    : {partial_brand:4d}  ({partial_brand/total_brand*100:.1f}%)")
    print(f"  Not covered          : {none_brand:4d}  ({none_brand/total_brand*100:.1f}%)")
    print(f"  ── Coverage          : {covered_brand/total_brand*100:.1f}%")
    print("=" * 68)

    # Fuzzy matches — worth reviewing
    fuzzy = {k: v for k, v in dci_results.items() if v["match_type"] == "fuzzy"}
    if fuzzy:
        print(f"\n── Fuzzy matches ({len(fuzzy)}) — please review ─────────────────────")
        for raw, r in sorted(fuzzy.items(), key=lambda x: -x[1]["score"]):
            print(f"  [{r['score']:3.0f}]  {raw:50s} → {r['matched_to']}")

    # Not found
    missing = {k: v for k, v in dci_results.items() if v["match_type"] == "no_match"}
    if missing:
        print(f"\n── Not found ({len(missing)}) ──────────────────────────────────────")
        for raw in sorted(missing):
            combo_note = ""
            r = missing[raw]
            if r.get("is_combination"):
                found_parts   = [p["dci_raw"] for p in r["parts"] if p["match_type"] != "no_match"]
                missing_parts = [p["dci_raw"] for p in r["parts"] if p["match_type"] == "no_match"]
                combo_note = f"  (combo — missing: {', '.join(missing_parts)})"
            print(f"  {raw}{combo_note}")

    print()


def save_results(dci_results: dict, brand_rows: list):
    # Brand-level CSV
    pd.DataFrame(brand_rows).sort_values(
        ["match_type", "brand"]
    ).to_csv("brand_coverage_report.csv", index=False)

    # DCI-level CSV (flatten combination parts)
    dci_rows = []
    for raw, r in dci_results.items():
        if r.get("is_combination"):
            for part in r["parts"]:
                dci_rows.append({
                    "dci_raw":        raw,
                    "component":      part["dci_raw"],
                    "is_combination": True,
                    "matched_to":     part.get("matched_to"),
                    "label":          part.get("label"),
                    "match_type":     part["match_type"],
                    "score":          part["score"],
                })
        else:
            dci_rows.append({
                "dci_raw":        raw,
                "component":      raw,
                "is_combination": False,
                "matched_to":     r.get("matched_to"),
                "label":          r.get("label"),
                "match_type":     r["match_type"],
                "score":          r.get("score", 0),
            })

    pd.DataFrame(dci_rows).sort_values(
        ["match_type", "dci_raw"]
    ).to_csv("dci_coverage_report.csv", index=False)

    print("Saved → brand_coverage_report.csv")
    print("Saved → dci_coverage_report.csv")


def main():
    print("Loading brand→DCI map …")
    with open(JSON_PATH, encoding="utf-8") as f:
        brand_map = json.load(f)
    print(f"  {len(brand_map)} brands, {len(set(brand_map.values()))} unique DCIs\n")

    print("Connecting to Neo4j …")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("  Connected\n")

    print("Loading graph node names …")
    graph = load_graph_names(driver)
    print(f"  {len(graph)} nodes loaded\n")

    print("Running coverage check …")
    dci_results, brand_rows = check_coverage(brand_map, graph, FUZZY_THRESHOLD)

    print_report(dci_results, brand_rows)
    save_results(dci_results, brand_rows)

    driver.close()


if __name__ == "__main__":
    main()