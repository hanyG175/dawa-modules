import os
import sys
import json
from pathlib import Path

# Setup sys.path so core modules can be imported directly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.drug_normalizer import DrugNormalizer
from core.ddi_checker import DDIChecker

def main():
    print("Initializing components...")
    
    # Needs environment variables for Neo4j
    # You can set them here manually for testing if not set in your environment
    # os.environ["NEO4J_URI"] = "neo4j+s://6c51198a.databases.neo4j.io"
    # os.environ["NEO4J_USER"] = "neo4j"
    # os.environ["NEO4J_PASSWORD"] = "your_password"
    
    normalizer = DrugNormalizer()
    checker = DDIChecker()

    # E.g. someone inputs exactly two drugs
    input_drugs = ["Doliprane", "Augmentin"]
    print(f"\nProcessing input: {input_drugs}")
    
    normalized_list = []
    for drug in input_drugs:
        n = normalizer.normalize(drug)
        normalized_list.append(n)
        print(f" - {drug} -> INN: {n.get('english_inn', 'N/A')}")
        
    print("\nChecking Interactions (will use OpenFDA and ANSM Neo4j if configured)...")
    results = checker.fetch_all_context(normalized_list)
    
    print("\n--- RESULTS ---")
    print(results.get("text", "No interaction text."))
    
    print("\n--- STRUCTURED PAIRS ---")
    print(json.dumps(results.get("ansm_pairs", []), indent=2))

if __name__ == "__main__":
    main()
