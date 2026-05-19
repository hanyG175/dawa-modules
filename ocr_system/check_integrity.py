"""
Coverage checker: how many unique drug names in drug_interactions.csv
can be found as a Substance or Class node in the ANSM Neo4j graph?

Matching strategy (in order):
  1. Exact match after normalisation (lowercase, collapse spaces, fix hyphens)
  2. Fuzzy match using rapidfuzz for near-misses (accents, minor typos)

Requirements:
    pip install neo4j pandas rapidfuzz
"""

import re
import pandas as pd
from neo4j import GraphDatabase
from rapidfuzz import process, fuzz

# ── Config — fill in your Aura credentials ───────────────────────────────────
NEO4J_URI      = "neo4j+s://6c51198a.databases.neo4j.io"   # your Aura URI
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "iG2wNnspn5U91akemAvUI_TZskhTEX5ZTNDwDionEk4"

DDI_CSV        = "data/drug_interactions.csv"   # path to your file
FUZZY_THRESHOLD = 88   # 0-100; lower = more lenient matches
# ─────────────────────────────────────────────────────────────────────────────


def normalise(s: str) -> str:
    """Lowercase, collapse whitespace, fix hyphen artifacts."""
    s = s.strip().lower()
    s = re.sub(r"-\s+", "-", s)
    s = re.sub(r"\s{2,}", " ", s)
    return s


def load_ddi_names(path: str) -> dict[str, str]:
    """
    Returns {normalised_name: original_name} for every unique drug name
    in drug_a and drug_b columns.
    """
    df = pd.read_csv(path)
    names = (
        set(df["drug_a"].dropna().str.strip()) |
        set(df["drug_b"].dropna().str.strip())
    )
    return {normalise(n): n for n in names}


def load_graph_names(driver) -> dict[str, dict]:
    """
    Pulls all Substance and Class node names from Neo4j.
    Returns {normalised_name: {id, original_name, label}}
    """
    query = """
    MATCH (n)
    WHERE n:Substance OR n:Class
    RETURN
      CASE WHEN n:Substance THEN n.substanceId ELSE n.classId END AS id,
      n.name AS name,
      labels(n)[0] AS label
    """
    graph = {}
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            norm = normalise(record["name"])
            graph[norm] = {
                "id":    record["id"],
                "name":  record["name"],
                "label": record["label"],
            }
    return graph


def run_coverage_check(ddi_names: dict, graph_names: dict, fuzzy_threshold: int):
    """
    Match DDI names against graph names.
    Returns (exact_matches, fuzzy_matches, unmatched) as lists of dicts.
    """
    exact_matches  = []
    fuzzy_matches  = []
    unmatched      = []

    graph_norm_list = list(graph_names.keys())   # for fuzzy search

    for norm_ddi, orig_ddi in sorted(ddi_names.items()):

        # 1. Exact match
        if norm_ddi in graph_names:
            exact_matches.append({
                "ddi_name":    orig_ddi,
                "graph_name":  graph_names[norm_ddi]["name"],
                "graph_label": graph_names[norm_ddi]["label"],
                "graph_id":    graph_names[norm_ddi]["id"],
                "match_type":  "exact",
                "score":       100,
            })
            continue

        # 2. Fuzzy match
        best = process.extractOne(
            norm_ddi,
            graph_norm_list,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=fuzzy_threshold,
        )
        if best:
            matched_norm, score, _ = best
            fuzzy_matches.append({
                "ddi_name":    orig_ddi,
                "graph_name":  graph_names[matched_norm]["name"],
                "graph_label": graph_names[matched_norm]["label"],
                "graph_id":    graph_names[matched_norm]["id"],
                "match_type":  "fuzzy",
                "score":       score,
            })
        else:
            unmatched.append({
                "ddi_name":    orig_ddi,
                "graph_name":  None,
                "graph_label": None,
                "graph_id":    None,
                "match_type":  "no_match",
                "score":       0,
            })

    return exact_matches, fuzzy_matches, unmatched


def print_report(exact, fuzzy, unmatched):
    total   = len(exact) + len(fuzzy) + len(unmatched)
    covered = len(exact) + len(fuzzy)

    print("=" * 65)
    print("  ANSM Graph Coverage Report")
    print("=" * 65)
    print(f"  Total unique drug names in DDI file : {total}")
    print(f"  Exact matches                        : {len(exact)}")
    print(f"  Fuzzy matches  (≥{FUZZY_THRESHOLD}% similarity)   : {len(fuzzy)}")
    print(f"  Not found                            : {len(unmatched)}")
    print(f"  Coverage                             : {covered/total*100:.1f}%")
    print("=" * 65)

    if fuzzy:
        print(f"\n── Fuzzy matches ({len(fuzzy)}) ─────────────────────────────────")
        for m in sorted(fuzzy, key=lambda x: -x["score"]):
            print(f"  [{m['score']:3.0f}]  {m['ddi_name']:45s} → {m['graph_name']}")

    if unmatched:
        print(f"\n── Not found ({len(unmatched)}) ──────────────────────────────────")
        for m in sorted(unmatched, key=lambda x: x["ddi_name"]):
            print(f"  {m['ddi_name']}")

    print()


def save_results(exact, fuzzy, unmatched, path="coverage_report.csv"):
    all_rows = exact + fuzzy + unmatched
    df = pd.DataFrame(all_rows, columns=[
        "ddi_name", "graph_name", "graph_label", "graph_id",
        "match_type", "score"
    ])
    df.sort_values(["match_type", "ddi_name"], inplace=True)
    df.to_csv(path, index=False)
    print(f"Full results saved → {path}")


def main():
    print("Loading DDI drug names …")
    ddi_names = load_ddi_names(DDI_CSV)
    print(f"  {len(ddi_names)} unique names found\n")

    print("Connecting to Neo4j …")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    driver.verify_connectivity()
    print("  Connected\n")

    print("Loading graph node names …")
    graph_names = load_graph_names(driver)
    print(f"  {len(graph_names)} nodes loaded\n")

    print("Running coverage check …")
    exact, fuzzy, unmatched = run_coverage_check(ddi_names, graph_names, FUZZY_THRESHOLD)

    print_report(exact, fuzzy, unmatched)
    save_results(exact, fuzzy, unmatched, "coverage_report.csv")

    driver.close()


if __name__ == "__main__":
    main()