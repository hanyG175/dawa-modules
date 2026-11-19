import json

def main():
    in_file = "brand_to_brand_interactions_fast.json"
    out_file = "brand_to_brand_interactions_simple.json"
    
    with open(in_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    simple_map = {}
    for brand, inters in data.items():
        targets = list(set([inter["target_brand"] for inter in inters]))
        targets.sort()
        simple_map[brand] = targets
        
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(simple_map, f, indent=4, ensure_ascii=False)
        
    print(f"Created simplified map in {out_file} for {len(simple_map)} brands.")

if __name__ == "__main__":
    main()
