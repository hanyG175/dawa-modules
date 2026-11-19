import json
import re
from neo4j import GraphDatabase

import check_graph_dz

NEO4J_URI      = "neo4j+s://e1c97a5d.databases.neo4j.io"
NEO4J_USER     = "e1c97a5d"
NEO4J_PASSWORD = "Y3Zseok0X_PiX3T_V559UEoYIDjU7t2sxFWi2EFFLWM"
JSON_PATH       = "data/nomenclature_brand_to_dci.json"

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    query = """
    MATCH (n)-[:BELONGS_TO*0..1]->(m)-[:INTERACTS_WITH]-()
    WHERE n:Substance OR n:Class
    RETURN n.name AS name
    """
    
    interacting_graph_names = set()
    with driver.session() as session:
        for rec in session.run(query):
            name = rec["name"]
            if name:
                interacting_graph_names.add(check_graph_dz.normalise(name))
                
    with open(JSON_PATH, encoding="utf-8") as f:
        brand_map = json.load(f)
        
    graph = check_graph_dz.load_graph_names(driver)
    dci_results, brand_rows = check_graph_dz.check_coverage(brand_map, graph, 88)
    
    interacting_brands = []
    
    for row in brand_rows:
        match_type = row["match_type"]
        if match_type in ("exact", "fuzzy", "partial"):
            dci_raw = row["dci"]
            r = dci_results[dci_raw]
            
            is_interacting = False
            if r.get("is_combination"):
                for part in r["parts"]:
                    if part["match_type"] != "no_match":
                        norm_matched = check_graph_dz.normalise(part["matched_to"])
                        if norm_matched in interacting_graph_names:
                            is_interacting = True
                            break
            else:
                if r["match_type"] != "no_match":
                    norm_matched = check_graph_dz.normalise(r["matched_to"])
                    if norm_matched in interacting_graph_names:
                        is_interacting = True
                        
            if is_interacting:
                interacting_brands.append(row["brand"])

    # save to list
    out_file = "interacting_algerian_brands.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for b in sorted(list(set(interacting_brands))):
            f.write(f"{b}\n")
            
    print(f"Saved {len(set(interacting_brands))} interacting brands to {out_file}.")
    driver.close()

if __name__ == "__main__":
    main()
