import subprocess
import os
import json

env = os.environ.copy()
env["PGPASSWORD"] = "vectordb123"
env["PGCLIENTENCODING"] = "UTF8"

conn = "-h 192.168.3.146 -p 5432 -U vectordb -d vectordb"

tables = [
    "chat_history",
    "chunks",
    "config_data",
    "documents",
    "policy_documents",
    "sales_import",
    "tech_data",
    "chunks_bak",
    "documents_bak",
]

output = {}
for tbl in tables:
    result = subprocess.run(
        f'chcp 65001 > $null; psql {conn} -c "\\d {tbl}"',
        shell=True, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    output[tbl] = result.stdout

print(json.dumps(output, ensure_ascii=False, indent=2))
