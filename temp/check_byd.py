import psycopg2
from psycopg2.extras import RealDictCursor
import sys

try:
    conn = psycopg2.connect(host='192.168.3.146', port=5432, dbname='vectordb', user='postgres', password='postgres', connect_timeout=5)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # 1. 看 sales_import 表结构
    cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='sales_import' ORDER BY ordinal_position")
    print('=== schema ===')
    for r in cur.fetchall(): print(dict(r))

    # 2. 看月份范围
    cur.execute('SELECT MIN(period) AS min_p, MAX(period) AS max_p, COUNT(*) AS total_rows, COUNT(DISTINCT period) AS distinct_periods FROM sales_import')
    print('=== range ==='); print(dict(cur.fetchone()))

    # 3. 看 2026 数据
    cur.execute("SELECT period, COUNT(*) AS rows FROM sales_import WHERE period LIKE '2026%' GROUP BY period ORDER BY period")
    print('=== 2026 months ===')
    for r in cur.fetchall(): print(dict(r))

    # 4. 看品牌字段样例 (2026)
    cur.execute("SELECT DISTINCT brand FROM sales_import WHERE period LIKE '2026%' LIMIT 20")
    print('=== sample brands 2026 ===')
    for r in cur.fetchall(): print(repr(dict(r)))

    # 5. 试 LIKE '%BYD%'
    cur.execute("SELECT period, brand, SUM(sales_volume) AS vol FROM sales_import WHERE brand LIKE '%BYD%' GROUP BY period, brand ORDER BY period")
    print('=== LIKE %BYD% ===')
    rows = cur.fetchall()
    print('row count:', len(rows))
    for r in rows[:10]: print(dict(r))

    # 6. SUBSTR mojibake BYD
    cur.execute("SELECT period, brand, SUM(sales_volume) AS vol FROM sales_import WHERE SUBSTR(brand, 1, 2) = '姣斾簹' GROUP BY period, brand ORDER BY period")
    print('=== SUBSTR brand[1:2]=姣斾簹 (BYD mojibake) ===')
    rows = cur.fetchall()
    print('row count:', len(rows))
    for r in rows[:20]: print(dict(r))

    # 7. 试 BYD 各 period 累计 (如果品牌用 mojibake)
    cur.execute("SELECT period, SUM(sales_volume) AS vol FROM sales_import WHERE SUBSTR(brand, 1, 2) = '姣斾簹' GROUP BY period ORDER BY period")
    print('=== BYD (mojibake) by period ===')
    for r in cur.fetchall(): print(dict(r))

    # 8. 试用户假设的 SQL
    cur.execute("SELECT brand, period, SUM(sales_volume) AS vol FROM sales_import WHERE brand LIKE '%BYD%' AND period BETWEEN '2026-01' AND '2026-03' GROUP BY period, brand ORDER BY period")
    print('=== user SQL: LIKE %BYD% BETWEEN 2026-01 AND 2026-03 ===')
    rows = cur.fetchall()
    print('row count:', len(rows))
    for r in rows[:10]: print(dict(r))

    cur.close(); conn.close()
except Exception as e:
    print(f'ERROR: {type(e).__name__}: {e}', file=sys.stderr)
    sys.exit(1)
