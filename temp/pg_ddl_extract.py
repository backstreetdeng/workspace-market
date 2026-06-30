import subprocess
import os

env = os.environ.copy()
env["PGPASSWORD"] = "vectordb123"

conn = "-h 192.168.3.146 -p 5432 -U vectordb -d vectordb"

tables = [
    "chat_history",
    "chunks",
    "chunks_bak",
    "config_data",
    "documents",
    "documents_bak",
    "policy_documents",
    "sales_import",
    "tech_data",
]

for tbl in tables:
    print(f"\n{'='*60}")
    print(f"-- Table: {tbl}")
    print(f"{'='*60}")
    result = subprocess.run(
        f'psql {conn} -c "\\d {tbl}"',
        shell=True, env=env, capture_output=True, text=True
    )
    print(result.stdout)
