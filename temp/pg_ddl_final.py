import psycopg2

conn = psycopg2.connect(
    host="192.168.3.146",
    port=5432,
    database="vectordb",
    user="vectordb",
    password="vectordb123"
)
conn.set_client_encoding('UTF8')
cur = conn.cursor()

tables = [
    "chat_history",
    "chunks",
    "config_data",
    "documents",
    "policy_documents",
    "sales_import",
    "tech_data",
]

results = {}

for tbl in tables:
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position
    """, (tbl,))
    cols = cur.fetchall()

    cur.execute("""
        SELECT a.attname
        FROM pg_constraint c
        JOIN pg_class cl ON c.conrelid = cl.oid
        JOIN pg_namespace n ON n.oid = cl.relnamespace
        JOIN pg_attribute a ON a.attrelid = cl.oid AND a.attnum = ANY(c.conkey)
        WHERE cl.relname = %s AND n.nspname = 'public' AND c.contype = 'p'
    """, (tbl,))
    pk_cols = [r[0] for r in cur.fetchall()]

    cur.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = %s AND schemaname = 'public'
    """, (tbl,))
    indexes = cur.fetchall()

    results[tbl] = {
        "columns": [
            {
                "name": c[0],
                "type": c[1],
                "max_length": c[2],
                "nullable": c[3],
                "default": c[4]
            } for c in cols
        ],
        "primary_keys": pk_cols,
        "indexes": [{"name": i[0], "def": i[1]} for i in indexes if "pkey" not in i[0].lower()]
    }

# Pretty print
for tbl, info in results.items():
    print(f"\n{'='*60}")
    print(f"CREATE TABLE {tbl} (")

    # Get column widths
    name_w = max(len(c["name"]) for c in info["columns"]) + 2
    type_w = max(len(c["type"]) for c in info["columns"]) + 2

    for col in info["columns"]:
        nullable = "NOT NULL" if col["nullable"] == "NO" else ""
        default = f" DEFAULT {col['default']}" if col["default"] else ""
        length = f"({col['max_length']})" if col["max_length"] else ""
        print(f"  {col['name']:<25} {col['type']:<30}{length:<8}{nullable:<12}{default}")

    if info["primary_keys"]:
        print(f"  PRIMARY KEY ({', '.join(info['primary_keys'])})")
    print(");")
    for idx in info["indexes"]:
        print(f"{idx['def']};")

conn.close()
