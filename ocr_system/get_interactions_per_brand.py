import json
import check_graph_dz
from neo4j import GraphDatabase

NEO4J_URI      = "neo4j+s://e1c97a5d.databases.neo4j.io"
NEO4J_USER     = "e1c97a5d"
NEO4J_PASSWORD = "Y3Zseok0X_PiX3T_V559UEoYIDjU7t2sxFWi2EFFLWM"
JSON_PATH       = "data/nomenclature_brand_to_dci.json"

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    query = """
    MATCH (n)-[:BELONGS_TO*0..1]->(n1)-[r:INTERACTS_WITH]-(n2)
    WHERE n:Substance OR n:Class
    RETURN n.name AS source, n2.name AS target, r.severity AS severity, r.risk AS risk
    """
    print("Fetching interactions from Neo4j...")
    
    interactions_map = {}
    with driver.session() as session:
        for rec in session.run(query):
            src = check_graph_dz.normalise(rec["source"])
            tgt = rec["target"]
            sev = rec["severity"]
            risk = rec["risk"]
            if src not in interactions_map:
                interactions_map[src] = []
            interactions_map[src].append({"target": tgt, "severity": sev, "risk": risk})
            
    print("Loaded interactions map.")
    
    with open(JSON_PATH, encoding="utf-8") as f:
        brand_map = json.load(f)
        
    graph = check_graph_dz.load_graph_names(driver)
    dci_results, brand_rows = check_graph_dz.check_coverage(brand_map, graph, 88)
    
    brand_interactions = {}
    
    for row in brand_rows:
        brand = row["brand"]
        match_type = row["match_type"]
        if match_type in ("exact", "fuzzy", "partial"):
            dci_raw = row["dci"]
            r = dci_results[dci_raw]
            
            b_interactions = []
            
            if r.get("is_combination"):
                for part in r["parts"]:
                    if part["match_type"] != "no_match":
                        norm_matched = check_graph_dz.normalise(part["matched_to"])
                        if norm_matched in interactions_map:
                            b_interactions.extend(interactions_map[norm_matched])
            else:
                if r["match_type"] != "no_match":
                    norm_matched = check_graph_dz.normalise(r["matched_to"])
                    if norm_matched in interactions_map:
                        b_interactions.extend(interactions_map[norm_matched])
                        
            if b_interactions:
                # Deduplicate
                seen = set()
                dedup = []
                for inter in b_interactions:
                    k = (inter["target"], inter["severity"], inter["risk"])
                    if k not in seen:
                        seen.add(k)
                        dedup.append(inter)
                brand_interactions[brand] = dedup

    out_file = "algerian_brands_interactions.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(brand_interactions, f, indent=4, ensure_ascii=False)
        
    print(f"Saved interactions for {len(brand_interactions)} brands to {out_file}.")
    driver.close()

if __name__ == "__main__":
    main()
