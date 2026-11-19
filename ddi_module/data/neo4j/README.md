# Neo4j graph exports

These CSV files are the node and relationship exports used to populate or inspect the Neo4j graph behind the DDI checks.

```text
neo4j_nodes_classes.csv
neo4j_nodes_interactions.csv
neo4j_nodes_substances.csv
neo4j_rels_belongs_to.csv
neo4j_rels_involves.csv
```

The application connects to Neo4j through `NEO4J_URI`, `NEO4J_USER` or `NEO4J_USERNAME`, `NEO4J_PASSWORD`, and optionally `NEO4J_DATABASE`. These files are reference exports, not a substitute for the running database. Keep their provenance and license with any public release.