import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DB = {"host": "192.168.3.146", "port": 5432, "database": "vectordb", "user": "vectordb", "password": "vectordb123"}

try:
    conn = psycopg2.connect(**DB, connect_timeout=5, cursor_factory=RealDictCursor)
    cur = conn.cursor()

    # 1. Schema
    cur.execute("""SELECT column_name, data_type, ordinal_position
                   FROM information_schema.columns
                   WHERE table_name='sales_import' ORDER BY ordinal_position""")
    print('=== schema (sales_import) ===')
    for r in cur.fetchall(): print(f"  col{r['ordinal_position']:>3} {r['column_name']!r:30} {r['data_type']}")

    # 2. range
    cur.execute('SELECT MIN(period) AS min_p, MAX(period) AS max_p, COUNT(*) AS rows FROM sales_import')
    print('=== range ==='); print(' ', dict(cur.fetchone()))

    # 3. 2026 months
    cur.execute("SELECT period, COUNT(*) AS rows FROM sales_import WHERE period LIKE '2026%' GROUP BY period ORDER BY period")
    print('=== 2026 months ===')
    for r in cur.fetchall(): print(' ', dict(r))

    # 4. sample distinct brand values 2026
    cur.execute("SELECT DISTINCT brand FROM sales_import WHERE period LIKE '2026%' LIMIT 30")
    print('=== distinct brands (2026, first 30) ===')
    for r in cur.fetchall(): print(f"  {r['brand']!r}")

    # 5. proposed SQL: LIKE %BYD% BETWEEN 2026-01 AND 2026-03
    cur.execute("""SELECT brand, period, SUM(sales_volume) AS vol
                   FROM sales_import
                   WHERE brand LIKE '%%BYD%%' AND period BETWEEN '2026-01' AND '2026-03'
                   GROUP BY brand, period ORDER BY period""")
    rows = cur.fetchall()
    print(f'=== proposed SQL: LIKE %BYD% BETWEEN 2026-01 AND 2026-03 -> rows={len(rows)} ===')
    for r in rows[:10]: print(' ', dict(r))

    # 6. SUBSTR mojibake BYD
    cur.execute("""SELECT brand, period, SUM(sales_volume) AS vol
                   FROM sales_import
                   WHERE SUBSTR(brand, 1, 2) = '姣斾簹'
                   GROUP BY brand, period ORDER BY period""")
    rows = cur.fetchall()
    print(f'=== SUBSTR(brand,1,2)=姣斾簹 (mojibake BYD) -> rows={len(rows)} ===')
    for r in rows[:20]: print(' ', dict(r))

    # 7. BYD 2026 累计（Jan+Feb）
    cur.execute("""SELECT period, SUM(sales_volume) AS vol
                   FROM sales_import
                   WHERE SUBSTR(brand, 1, 2) = '姣斾簹' AND period LIKE '2026%'
                   GROUP BY period ORDER BY period""")
    print('=== BYD (mojibake) 2026 by month ===')
    rows = cur.fetchall()
    for r in rows: print(' ', dict(r))
    if rows:
        total = sum(int(r['vol'] or 0) for r in rows)
        print(f'  TOTAL 2026 累计 = {total:,}')

    # 8. Top 10 brand ranking 2026 Jan+Feb (using SUBSTR mojibake)
    cur.execute("""SELECT SUBSTR(brand, 1, 2) AS brand_pref, SUM(sales_volume) AS vol
                   FROM sales_import
                   WHERE period IN ('202601', '202602')
                   GROUP BY SUBSTR(brand, 1, 2)
                   ORDER BY vol DESC LIMIT 10""")
    print('=== Top 10 brand_pref 2026 Jan+Feb ===')
    for r in cur.fetchall(): print(f"  {r['brand_pref']!r:20} {int(r['vol']):>10,}")

    cur.close(); conn.close()
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}', file=sys.stderr)
    import traceback; traceback.print_exc()
    sys.exit(1)
