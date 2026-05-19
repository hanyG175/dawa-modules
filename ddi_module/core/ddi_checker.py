import json
import requests
import pandas as pd
import itertools
import os
from pathlib import Path
from typing import Dict, List, Any
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None

class DDIChecker:
    """
    Handles fetching Drug-Drug Interactions (DDI) from external APIs (OpenFDA) and local ANSM Neo4j Graph.
    """

    def __init__(self):
        # Neo4j setup
        self.driver = None
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        if GraphDatabase:
            try:
                uri = os.getenv("NEO4J_URI", "").strip()
                username = (os.getenv("NEO4J_USERNAME") or os.getenv("NEO4J_USER") or "").strip()
                password = os.getenv("NEO4J_PASSWORD", "").strip()

                if not uri or not username or not password:
                    print("Neo4j disabled: missing NEO4J_URI / NEO4J_USERNAME (or NEO4J_USER) / NEO4J_PASSWORD environment variables.")
                    return

                self.driver = GraphDatabase.driver(uri, auth=(username, password))
                self.driver.verify_connectivity()
                print(f"Neo4j connected successfully: {uri} (db={self.neo4j_database})")
            except Exception as e:
                print(f"Error connecting to Neo4j: {e}")


    def check_ansm(self, drugs_dci_structs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Checks for pairwise interactions within the extracted drugs using Neo4j ANSM Graph."""
        if not self.driver or len(drugs_dci_structs) < 2:
            return {"text": "", "pairs": []}

        found_interactions = []
        structured_pairs = []

        try:
            with self.driver.session(database=self.neo4j_database) as session:
                for d_info1, d_info2 in itertools.combinations(drugs_dci_structs, 2):
                    d1_orig = d_info1.get("original_query", "").strip()
                    d2_orig = d_info2.get("original_query", "").strip()
                    
                    d1_parts = [p.strip().lower() for p in d_info1.get("dci_french", "").split('/') if p.strip()]
                    d2_parts = [p.strip().lower() for p in d_info2.get("dci_french", "").split('/') if p.strip()]
                    
                    if not d1_parts or not d2_parts:
                        continue

                    for d1_clean, d2_clean in itertools.product(d1_parts, d2_parts):
                        query = """
                        MATCH (d1:Substance) WHERE toLower(d1.name) CONTAINS $d1
                        MATCH (d2:Substance) WHERE toLower(d2.name) CONTAINS $d2
                        MATCH p = (d1)-[:BELONGS_TO*0..1]->(n1)-[r:INTERACTS_WITH]-(n2)<-[:BELONGS_TO*0..1]-(d2)
                        RETURN r.severity as severity, r.risk as risk, r.management as management, d1.name as drug_a, d2.name as drug_b, n1.name as target_1, n2.name as target_2
                        LIMIT 15
                        """
                        result = session.run(query, d1=d1_clean, d2=d2_clean)
                        
                        for record in result:
                            risk = str(record.get('risk', '')).strip()
                            management = str(record.get('management', '')).strip()
                            severity = str(record.get('severity', '')).strip()
                            drug_a_db = str(record.get('drug_a', d1_clean.upper()))
                            drug_b_db = str(record.get('drug_b', d2_clean.upper()))
                            target_1 = str(record.get('target_1', ''))
                            target_2 = str(record.get('target_2', ''))

                            interaction_context = f"{drug_a_db} x {drug_b_db}"
                            if target_1 != drug_a_db or target_2 != drug_b_db:
                                interaction_context += f" (via {target_1} x {target_2})"
                                
                            if risk and risk != 'nan':
                                desc = f"- ANSM [{interaction_context}] ({severity}): {risk} {management if management and management != 'nan' else ''}"
                                if desc not in found_interactions:
                                    found_interactions.append(desc)
                                    
                                    # Group by original input pair
                                    existing = next((p for p in structured_pairs if (p["original_a"].upper() == d1_orig.upper() and p["original_b"].upper() == d2_orig.upper()) or (p["original_a"].upper() == d2_orig.upper() and p["original_b"].upper() == d1_orig.upper())), None)
                                    
                                    if existing:
                                        if severity not in existing["severity"]:
                                            existing["severity"].append(severity)
                                        if risk not in existing["risk"]:
                                            existing["risk"].append(risk)
                                        if management and management != 'nan' and management not in existing["management"]:
                                            existing["management"].append(management)
                                        if target_1 and target_1 != drug_a_db and target_1 not in existing["class_a"]:
                                            existing["class_a"] += f", {target_1}"
                                        if target_2 and target_2 != drug_b_db and target_2 not in existing["class_b"]:
                                            existing["class_b"] += f", {target_2}"
                                    else:
                                        structured_pairs.append({
                                            "original_a": d1_orig.upper(),
                                            "original_b": d2_orig.upper(),
                                            "drug_a_dci": drug_a_db.upper(),
                                            "drug_b_dci": drug_b_db.upper(),
                                            "class_a": target_1 if target_1 != drug_a_db else "",
                                            "class_b": target_2 if target_2 != drug_b_db else "",
                                            "severity": [severity],
                                            "risk": [risk],
                                            "management": [management] if management and management != 'nan' else []
                                        })
        except Exception as e:
            print(f"Error querying Neo4j: {e}")

        if found_interactions:
            return {"text": "Thésaurus ANSM:\n" + "\n".join(found_interactions), "pairs": structured_pairs}
        return {"text": "Thésaurus ANSM: Aucune interaction formelle détectée entre ces molécules.", "pairs": []}
    def check_openfda(self, drug_name: str) -> str:
        """Fetches interaction data from OpenFDA API."""
        try:
            api_key = "bCJ7ykUPozw7jlixyA8i0MyKPuxszvg6sskKjol9"
            url = f'https://api.fda.gov/drug/label.json?api_key={api_key}&search=openfda.substance_name:"{drug_name}"&limit=1'
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                if results and "drug_interactions" in results[0]:
                    interactions = results[0]["drug_interactions"][0]
                    return interactions[:500] + "..." if len(interactions) > 500 else interactions
            return "Aucune information d'interaction trouvée sur OpenFDA."
        except Exception:
            return "Erreur lors de la connexion à OpenFDA."


    def fetch_all_context(self, normalized_drugs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Gather context from OpenFDA and ANSM Neo4j."""
        context_parts = []
        ansm_pairs = []

        expanded_inns = []
        for d in normalized_drugs:
            inn = d.get("english_inn", "")
            if "/" in inn:
                parts = [p.strip() for p in inn.split("/") if p.strip()]
                expanded_inns.extend(parts)
            elif inn:
                expanded_inns.append(inn.strip())

        if len(normalized_drugs) > 1:
            ansm_res = self.check_ansm(normalized_drugs)
            if ansm_res["text"]:
                context_parts.append(f"=== Interactions Croisées (ANSM) ===\n{ansm_res['text']}\n")
            ansm_pairs = ansm_res.get("pairs", [])

        context_parts.append("=== Mentions OpenFDA (Base Globale) ===")
        for inn in set(expanded_inns):
            fda_res = self.check_openfda(inn)
            if fda_res:
                context_parts.append(f"OpenFDA - {inn.upper()}: {fda_res}")

        return {
            "text": "\n".join(context_parts),
            "ansm_pairs": ansm_pairs
        }

