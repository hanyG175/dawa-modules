import json
from collections import defaultdict
from neo4j import GraphDatabase
import check_graph_dz

NEO4J_URI      = "neo4j+s://e1c97a5d.databases.neo4j.io"
NEO4J_USER     = "e1c97a5d"
NEO4J_PASSWORD = "Y3Zseok0X_PiX3T_V559UEoYIDjU7t2sxFWi2EFFLWM"
JSON_PATH       = "data/nomenclature_brand_to_dci.json"

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with open(JSON_PATH, encoding="utf-8") as f:
        brand_map = json.load(f)
        
    print("Loading graph names...")
    graph = check_graph_dz.load_graph_names(driver)
    
    print("Running DCI mapping...")
    dci_results, brand_rows = check_graph_dz.check_coverage(brand_map, graph, 88)
    
    name_to_brands = defaultdict(list)
    
    for row in brand_rows:
        brand = row["brand"]
        match_type = row["match_type"]
        if match_type in ("exact", "fuzzy", "partial"):
            dci_raw = row["dci"]
            r = dci_results[dci_raw]
            
            if r.get("is_combination"):
                for part in r["parts"]:
                    if part["match_type"] != "no_match":
                        gname = part["matched_to"]
                        if gname:
                            name_to_brands[gname].append(brand)
            else:
                if r["match_type"] != "no_match":
                    gname = r["matched_to"]
                    if gname:
                        name_to_brands[gname].append(brand)
                        
    unique_names = list(name_to_brands.keys())
    print(f"Total unique mapped graph names: {len(unique_names)}")
    
    query = """
    MATCH (sub1)-[:BELONGS_TO*0..3]->(n1)-[r:INTERACTS_WITH]-(n2)<-[:BELONGS_TO*0..3]-(sub2)
    WHERE sub1.name IN $unique_names AND sub2.name IN $unique_names
    RETURN sub1.name AS source_name, sub2.name AS target_name, r.severity AS severity, r.risk AS risk
    """
    
    print("Querying brand-to-brand interactions from Neo4j...")
    brand_to_brand = defaultdict(list)
    seen_interactions = set()
    
    with driver.session() as session:
        result = session.run(query, unique_names=unique_names)
        for rec in result:
            src_name = rec["source_name"]
            tgt_name = rec["target_name"]
            sev = rec["severity"]
            risk = rec["risk"]
            
            for brand_a in name_to_brands[src_name]:
                for brand_b in name_to_brands[tgt_name]:
                    if brand_a != brand_b:
                        key = (brand_a, brand_b, sev)
                        if key not in seen_interactions:
                            seen_interactions.add(key)
                            brand_to_brand[brand_a].append({
                                "target_brand": brand_b,
                                "severity": sev,
                                "risk": risk
                            })
                            
    out_file = "brand_to_brand_interactions.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(brand_to_brand, f, indent=4, ensure_ascii=False)
        
    print(f"Saved brand-to-brand interactions for {len(brand_to_brand)} brands to {out_file}.")
    driver.close()

if __name__ == "__main__":
    main()
