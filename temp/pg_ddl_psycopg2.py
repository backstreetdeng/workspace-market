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
    "chunks_bak",
    "documents_bak",
]

for tbl in tables:
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position
    """, (tbl,))
    cols = cur.fetchall()

    cur.execute("""
        SELECT conname, pg_get_expr(conbin, cl.relname::regclass)
        FROM pg_constraint c
        JOIN pg_class cl ON c.conrelid = cl.oid
        WHERE cl.relname = %s AND c.contype = 'p'
    """, (tbl,))
    pkeys = cur.fetchall()

    cur.execute("""
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE tablename = %s AND schemaname = 'public'
    """, (tbl,))
    indexes = cur.fetchall()

    print(f"\n{'='*60}")
    print(f"CREATE TABLE {tbl} (")
    for col in cols:
        col_name, data_type, max_len, nullable, default_val = col
        nullable_str = "NOT NULL" if nullable == "NO" else ""
        default_str = f" DEFAULT {default_val}" if default_val else ""
        length_str = f"({max_len})" if max_len else ""
        print(f"  {col_name:25} {data_type:25}{length_str:8}{nullable_str:12}{default_str}")
    if pkeys:
        for pk in pkeys:
            print(f"  PRIMARY KEY ({pk[1]})")
    print(");")
    for idx in indexes:
        idx_name, idx_def = idx
        if "pkey" not in idx_name.lower():
            print(f"{idx_def};")

conn.close()
