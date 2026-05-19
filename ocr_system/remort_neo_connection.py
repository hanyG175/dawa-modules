import socket
import threading
import queue
from urllib.parse import urlparse

from neo4j import GraphDatabase

STEP_TIMEOUT_SECONDS = 8


def run_with_timeout(func, timeout_seconds, step_name, *args, **kwargs):
    """Run a potentially blocking call in a daemon thread and fail fast on timeout."""
    q = queue.Queue(maxsize=1)

    def _target():
        try:
            res = func(*args, **kwargs)
            q.put((True, res))
        except Exception as ex:
            q.put((False, ex))

    t = threading.Thread(target=_target, daemon=True)
    t.start()
    t.join(timeout_seconds)

    if t.is_alive():
        raise TimeoutError(f"{step_name} timed out after {timeout_seconds}s")

    ok, payload = q.get()
    if ok:
        return payload
    raise payload

class DrugDatabase:
    def __init__(self, uri, user, password):
        # Keep timeouts short so failures don't look like a freeze.
        self.uri = uri
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            connection_timeout=5,
            connection_acquisition_timeout=5,
            max_transaction_retry_time=5,
            keep_alive=True,
        )

    def close(self):
        if self.driver:
            self.driver.close()

    def verify(self):
        """Fail fast if the server cannot be reached/authenticated."""
        self.driver.verify_connectivity()

    def get_drug_interactions(self, drug_name_a, drug_name_b):
        """
        Example query for your PFE: Find all interactions between two drugs.
        """
        query = """
        MATCH (d1:Substance) WHERE toLower(d1.name) CONTAINS toLower($drug_a)
        MATCH (d2:Substance) WHERE toLower(d2.name) CONTAINS toLower($drug_b)
        MATCH p = (d1)-[:BELONGS_TO*0..1]->(n1)-[r:INTERACTS_WITH]-(n2)<-[:BELONGS_TO*0..1]-(d2)
        RETURN r.severity as severity, r.risk as risk, r.management as management, d1.name as drug_a, d2.name as drug_b, n1.name as target_1, n2.name as target_2
        LIMIT 15
        """
        with self.driver.session(database="neo4j") as session:
            result = session.run(query, drug_a=drug_name_a, drug_b=drug_name_b)
            return [dict(record) for record in result]


def check_tcp(uri: str, timeout_seconds: int = 3):
    parsed = urlparse(uri)
    host = parsed.hostname
    port = parsed.port or 7687
    if not host:
        raise ValueError(f"Cannot parse host from URI: {uri}")

    with socket.create_connection((host, port), timeout=timeout_seconds):
        return host, port

# --- Usage ---
if __name__ == "__main__":
    # Remote Docker Neo4j Server
    URI = "bolt://172.16.1.45:7687"
    USER = "neo4j"
    PASSWORD = "estin2026"

    db = None
    try:
        socket.setdefaulttimeout(5)

        print("[1/4] TCP reachability check...", flush=True)
        host, port = check_tcp(URI, timeout_seconds=3)
        print(f"✓ TCP reachable: {host}:{port}", flush=True)

        print("[2/4] Creating Neo4j driver...", flush=True)
        db = DrugDatabase(URI, USER, PASSWORD)
        print("✓ Driver created", flush=True)

        print("[3/4] Verifying Neo4j connectivity/auth...", flush=True)
        run_with_timeout(db.verify, STEP_TIMEOUT_SECONDS, "Connectivity verification")
        print("✓ Neo4j connectivity OK", flush=True)

        print("[4/4] Running sample query (adalimumab + abatacept)...", flush=True)
        interactions = run_with_timeout(
            db.get_drug_interactions,
            STEP_TIMEOUT_SECONDS,
            "Sample query",
            "adalimumab",
            "abatacept",
        )

        if interactions:
            print(f"Found {len(interactions)} interactions:")
            for i, interaction in enumerate(interactions, 1):
                print(f"\n[{i}] Severity: {interaction.get('severity', 'N/A')}")
                print(f"    Risk: {interaction.get('risk', 'N/A')}")
                print(f"    Management: {interaction.get('management', 'N/A')}")
                print(f"    {interaction.get('drug_a', 'Drug A')} ↔ {interaction.get('drug_b', 'Drug B')}")
        else:
            print("No interactions found.")

    except Exception as e:
        print(f"✗ Connection or query failed: {e}")
        print("Safety stop triggered: script exited without waiting indefinitely.")
    finally:
        try:
            if db is not None:
                db.close()
                print("\n✓ Database connection closed")
        except Exception:
            pass
