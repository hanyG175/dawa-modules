import pandas as pd

# # Load your flat interactions CSV
# df = pd.read_csv('drug_interactions.csv')

# # 1. Create a unique ID for each interaction node
# df['interaction_id'] = ['INT_' + str(i).zfill(5) for i in range(len(df))]

# # 2. Extract the Interaction Nodes Table
# interactions_nodes = df[['interaction_id', 'severity', 'risk', 'management', 'compound', 'voir_aussi']].copy()
# # Save to CSV
# interactions_nodes.to_csv('neo4j_nodes_interactions.csv', index=False)

# # 3. Extract the Relationships Table (Interaction -> INVOLVES -> Drug/Class)
# # We melt drug_a and drug_b into a single column so we can easily map edges
# rels_a = df[['interaction_id', 'drug_a']].rename(columns={'drug_a': 'drug_name'})
# rels_b = df[['interaction_id', 'drug_b']].rename(columns={'drug_b': 'drug_name'})

# # Combine, drop nulls, and drop duplicates
# rels_involves = pd.concat([rels_a, rels_b]).dropna(subset=['drug_name']).drop_duplicates()
# rels_involves.to_csv('neo4j_rels_involves.csv', index=False)

# print(f"Created neo4j_nodes_interactions.csv with {len(interactions_nodes)} nodes.")
# print(f"Created neo4j_rels_involves.csv with {len(rels_involves)} relationships.")
df = pd.read_csv("neo4j_rels_involves.csv")
df["drug_name"] = df["drug_name"].str.lower().str.strip()
df.to_csv("neo4j_rels_involves.csv", index=False)