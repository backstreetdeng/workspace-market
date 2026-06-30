# -*- coding: utf-8 -*-
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(host="192.168.3.146", port=5432, database="vectordb", user="vectordb", password="vectordb123")
cur = conn.cursor(cursor_factory=RealDictCursor)

# Use attnum positions: brand=5, date=2, sales=13
cur.execute("""SELECT column_5_text AS brand, column_2_date AS month,
                      COUNT(*) AS rows, SUM(column_13_int) AS total_sales
               FROM (SELECT *,
                            (SELECT attname FROM pg_attribute
                             WHERE attrelid='sales_import'::regclass AND attnum=5) AS column_5_text,
                            (SELECT attname FROM pg_attribute
                             WHERE attrelid='sales_import'::regclass AND attnum=2) AS column_2_date,
                            (SELECT attname FROM pg_attribute
                             WHERE attrelid='sales_import'::regclass AND attnum=13) AS column_13_int
                     FROM sales_import LIMIT 5) t
               GROUP BY 1,2 LIMIT 5""")
for r in cur.fetchall(): print(r)
