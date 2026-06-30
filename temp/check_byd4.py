import psycopg2
from psycopg2.extras import RealDictCursor
import sys

DB = {"host": "192.168.3.146", "port": 5432, "database": "vectordb", "user": "vectordb", "password": "vectordb123"}

try:
    conn = psycopg2.connect(**DB, connect_timeout=5, cursor_factory=RealDictCursor)
    cur = conn.cursor()

    # Range
    cur.execute('SELECT MIN("销售日期") AS min_d, MAX("销售日期") AS max_d, COUNT(*) AS rows FROM sales_import')
    print('=== range ==='); print(' ', dict(cur.fetchone()))

    # 2026 months
    cur.execute("""SELECT "销售日期" AS period, COUNT(*) AS rows
                   FROM sales_import WHERE "销售日期" BETWEEN 202601 AND 202612
                   GROUP BY "销售日期" ORDER BY "销售日期" """)
    print('=== 2026 months ===')
    rows = cur.fetchall()
    for r in rows: print(' ', dict(r))

    # sample brands 2026 (first 30 distinct)
    cur.execute("""SELECT DISTINCT "产品商标" AS brand FROM sales_import
                   WHERE "销售日期" BETWEEN 202601 AND 202612 LIMIT 30""")
    print('=== distinct brands (2026, first 30) ===')
    for r in cur.fetchall(): print(f"  {r['brand']!r}")

    # user proposed SQL
    cur.execute("""SELECT "产品商标" AS brand, "销售日期" AS period, SUM("销量") AS vol
                   FROM sales_import
                   WHERE "产品商标" LIKE '%%BYD%%'
                   GROUP BY "产品商标", "销售日期" ORDER BY "销售日期" """)
    rows = cur.fetchall()
    print(f'=== LIKE %BYD% -> rows={len(rows)} ===')
    for r in rows[:10]: print(' ', dict(r))

    # SUBSTR mojibake BYD
    cur.execute("""SELECT "产品商标" AS brand, "销售日期" AS period, SUM("销量") AS vol
                   FROM sales_import
                   WHERE SUBSTR("产品商标", 1, 2) = '姣斾簹'
                   GROUP BY "产品商标", "销售日期" ORDER BY "销售日期" """)
    rows = cur.fetchall()
    print(f'=== SUBSTR(brand,1,2)=姣斾簹 (mojibake BYD) -> rows={len(rows)} ===')
    for r in rows[:20]: print(' ', dict(r))

    # BYD 2026 累计 by month
    cur.execute("""SELECT "销售日期" AS period, SUM("销量") AS vol
                   FROM sales_import
                   WHERE SUBSTR("产品商标", 1, 2) = '姣斾簹' AND "销售日期" BETWEEN 202601 AND 202612
                   GROUP BY "销售日期" ORDER BY "销售日期" """)
    rows = cur.fetchall()
    print('=== BYD (mojibake) 2026 by month ===')
    for r in rows: print(' ', dict(r))
    if rows:
        total = sum(int(r['vol'] or 0) for r in rows)
        print(f'  TOTAL 2026 累计 = {total:,}')

    # Top 10 brand_pref Jan+Feb 2026
    cur.execute("""SELECT SUBSTR("产品商标", 1, 2) AS brand_pref, SUM("销量") AS vol
                   FROM sales_import
                   WHERE "销售日期" IN (202601, 202602)
                   GROUP BY SUBSTR("产品商标", 1, 2)
                   ORDER BY vol DESC LIMIT 10""")
    print('=== Top 10 brand_pref 2026 Jan+Feb ===')
    for r in cur.fetchall(): print(f"  {r['brand_pref']!r:20} {int(r['vol']):>10,}")

    # Top 10 brand_pref 全 2026 (按当前已入库月份)
    cur.execute("""SELECT SUBSTR("产品商标", 1, 2) AS brand_pref, SUM("销量") AS vol
                   FROM sales_import
                   WHERE "销售日期" BETWEEN 202601 AND 202612
                   GROUP BY SUBSTR("产品商标", 1, 2)
                   ORDER BY vol DESC LIMIT 10""")
    print('=== Top 10 brand_pref 2026 (Jan+Feb only since 202603 not in DB) ===')
    for r in cur.fetchall(): print(f"  {r['brand_pref']!r:20} {int(r['vol']):>10,}")

    cur.close(); conn.close()
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}', file=sys.stderr)
    import traceback; traceback.print_exc()
    sys.exit(1)
