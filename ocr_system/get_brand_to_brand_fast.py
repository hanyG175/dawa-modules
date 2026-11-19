import json
from collections import defaultdict
from neo4j import GraphDatabase
import check_graph_dz

NEO4J_URI      = "neo4j+s://e1c97a5d.databases.neo4j.io"
NEO4J_USER     = "e1c97a5d"
NEO4J_PASSWORD = "Y3Zseok0X_PiX3T_V559UEoYIDjU7t2sxFWi2EFFLWM"

def main():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    # 1. Load the brand -> target interactions we already generated
    with open("algerian_brands_interactions.json", encoding="utf-8") as f:
        brand_inter_map = json.load(f)
        
    unique_targets = set()
    for brand, inters in brand_inter_map.items():
        for inter in inters:
            unique_targets.add(inter["target"])
            
    unique_targets = list(unique_targets)
    print(f"Total unique interaction targets (classes or substances): {len(unique_targets)}")
    
    # 2. Query Neo4j to resolve these targets to specific substances
    query = """
    UNWIND $targets AS tgt
    MATCH (sub:Substance)-[:BELONGS_TO*0..3]->(n)
    WHERE n.name = tgt
    RETURN n.name AS target, sub.name AS substance
    """
    
    target_to_substances = defaultdict(set)
    print("Resolving targets to substances in Neo4j...")
    with driver.session() as session:
        # We process in chunks to avoid huge query parameters if it's too big, 
        # but 1000 items in UNWIND is perfectly fine for Neo4j.
        chunk_size = 500
        for i in range(0, len(unique_targets), chunk_size):
            chunk = unique_targets[i:i+chunk_size]
            result = session.run(query, targets=chunk)
            for rec in result:
                tgt = rec["target"]
                sub = check_graph_dz.normalise(rec["substance"])
                target_to_substances[tgt].add(sub)
                
    # 3. Load Brand -> Substance mapping using check_graph_dz
    with open("data/nomenclature_brand_to_dci.json", encoding="utf-8") as f:
        brand_map = json.load(f)
        
    print("Loading graph names for mapping...")
    graph = check_graph_dz.load_graph_names(driver)
    
    print("Running DCI mapping...")
    dci_results, brand_rows = check_graph_dz.check_coverage(brand_map, graph, 88)
    
    # Build reverse map: substance (normalized) -> list of brands
    substance_to_brands = defaultdict(list)
    for row in brand_rows:
        brand = row["brand"]
        match_type = row["match_type"]
        if match_type in ("exact", "fuzzy", "partial"):
            dci_raw = row["dci"]
            r = dci_results[dci_raw]
            
            if r.get("is_combination"):
                for part in r["parts"]:
                    if part["match_type"] != "no_match":
                        gname = check_graph_dz.normalise(part["matched_to"])
                        if gname:
                            substance_to_brands[gname].append(brand)
            else:
                if r["match_type"] != "no_match":
                    gname = check_graph_dz.normalise(r["matched_to"])
                    if gname:
                        substance_to_brands[gname].append(brand)
                        
    # 4. Construct the final Brand -> Brand interactions
    print("Constructing final brand-to-brand map...")
    brand_to_brand = defaultdict(list)
    seen_interactions = set()
    
    for brand_a, inters in brand_inter_map.items():
        for inter in inters:
            tgt = inter["target"]
            sev = inter["severity"]
            risk = inter["risk"]
            
            # For this target, what substances does it contain?
            for sub in target_to_substances.get(tgt, set()):
                # For this substance, what brands contain it?
                for brand_b in substance_to_brands.get(sub, []):
                    if brand_a != brand_b:
                        key = (brand_a, brand_b, sev)
                        if key not in seen_interactions:
                            seen_interactions.add(key)
                            brand_to_brand[brand_a].append({
                                "target_brand": brand_b,
                                "severity": sev,
                                "risk": risk,
                                "original_target_class": tgt
                            })
                            
    out_file = "brand_to_brand_interactions_fast.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(brand_to_brand, f, indent=4, ensure_ascii=False)
        
    print(f"Saved brand-to-brand interactions for {len(brand_to_brand)} brands to {out_file}.")
    driver.close()

if __name__ == "__main__":
    main()
