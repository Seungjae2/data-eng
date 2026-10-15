# sql_analysis.py — 1~7단계를 이 파일에 이어 붙입니다
import duckdb
import pandas as pd

print(duckdb.sql("""
    SELECT user_id, count(*) AS buys, sum(value) AS spend
    FROM 'events.parquet'
    WHERE event_type = 'buy'
    GROUP BY user_id
    ORDER BY spend DESC
    LIMIT 5
"""))

# 2단계 — sql_analysis.py 끝에 이어 붙입니다
sql_result = duckdb.sql("""
    SELECT c.region,
           count(*)                  AS orders,
           sum(o.price * o.quantity) AS total
    FROM 'orders_step1.parquet' AS o
    JOIN 'customers.csv'        AS c
      ON o.customer_id = c.customer_id
    GROUP BY c.region
    ORDER BY total DESC
""").df()
print(sql_result)

# 3단계 — sql_analysis.py 끝에 이어 붙입니다 (sql_result 는 2단계에서 만들었습니다)
pd_result = (pd.read_parquet('orders_enriched.parquet')
             .groupby('region')
             .agg(orders=('order_id', 'count'),
                  total=('amount', 'sum'))
             .reset_index()
             .sort_values('total', ascending=False))
print(pd_result)

# 지역별 total을 대조
merged = sql_result.merge(pd_result, on='region', suffixes=('_sql', '_pd'))
merged['diff'] = merged['total_sql'] - merged['total_pd']
print(merged[['region', 'total_sql', 'total_pd', 'diff']])

# 4단계 — sql_analysis.py 끝에 이어 붙입니다
print(duckdb.sql("""
    WITH daily AS (
        SELECT date_trunc('day', ts) AS d, sum(value) AS revenue
        FROM 'events.parquet'
        WHERE event_type = 'buy'
        GROUP BY d
    )
    SELECT d, revenue,
           sum(revenue) OVER (ORDER BY d) AS cum_revenue
    FROM daily
    ORDER BY d
    LIMIT 5
"""))

# 4단계(CTE 따로 보기) — sql_analysis.py 끝에 이어 붙입니다
print(duckdb.sql("""
    SELECT date_trunc('day', ts) AS d, sum(value) AS revenue
    FROM 'events.parquet'
    WHERE event_type = 'buy'
    GROUP BY d
    ORDER BY d
    LIMIT 3
"""))

# 5단계(일부러 실패) — sql_analysis.py 끝에 이어 붙입니다
# 윈도 함수 결과(rnk)를 WHERE 로 거르면?
try:
    duckdb.sql("""
        SELECT o.customer_id,
               rank() OVER (ORDER BY o.price DESC) AS rnk
        FROM 'orders_step1.parquet' AS o
        WHERE rnk <= 3
    """).fetchall()
except Exception as e:
    print('예상대로 실패:', e)

# 5단계 — sql_analysis.py 끝에 이어 붙입니다
print(duckdb.sql("""
    WITH by_customer AS (
        SELECT c.region, o.customer_id,
               sum(o.price * o.quantity) AS total
        FROM 'orders_step1.parquet' AS o
        JOIN 'customers.csv'        AS c
          ON o.customer_id = c.customer_id
        GROUP BY c.region, o.customer_id
    )
    SELECT region, customer_id, total,
           rank() OVER (PARTITION BY region ORDER BY total DESC) AS rnk
    FROM by_customer
    QUALIFY rnk <= 3
    ORDER BY region, rnk
"""))

# 5단계(CTE 방식) — sql_analysis.py 끝에 이어 붙입니다. QUALIFY 없이 2-2 방식으로도 같은 결과
print(duckdb.sql("""
    WITH by_customer AS (
        SELECT c.region, o.customer_id, sum(o.price * o.quantity) AS total
        FROM 'orders_step1.parquet' AS o
        JOIN 'customers.csv' AS c ON o.customer_id = c.customer_id
        GROUP BY c.region, o.customer_id
    ),
    ranked AS (
        SELECT *, rank() OVER (PARTITION BY region ORDER BY total DESC) AS rnk
        FROM by_customer
    )
    SELECT * FROM ranked WHERE rnk <= 3 ORDER BY region, rnk
"""))


# 6단계 — sql_analysis.py 끝에 이어 붙입니다
print(duckdb.sql("""
    WITH daily AS (
        SELECT date_trunc('day', ts) AS d, sum(value) AS revenue
        FROM 'events.parquet'
        WHERE event_type = 'buy'
        GROUP BY d
    )
    SELECT d, revenue,
           round(avg(revenue) OVER (
               ORDER BY d ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
           )) AS ma7
    FROM daily
    ORDER BY d
    LIMIT 10
"""))


# 7단계 — sql_analysis.py 끝에 이어 붙입니다
# GROUP BY ALL — 집계가 아닌 열로 알아서 묶어 줍니다
print(duckdb.sql("""
    SELECT event_type, date_trunc('day', ts) AS d, count(*) AS cnt
    FROM 'events.parquet'
    GROUP BY ALL
    ORDER BY d, event_type
    LIMIT 5
"""))

# SELECT * EXCLUDE — 몇 개만 빼고 전부
print(duckdb.sql("SELECT * EXCLUDE (event_id) FROM 'events.parquet' LIMIT 3"))

# 열 이름 패턴으로 집계
print(duckdb.sql("SELECT max(COLUMNS('^value$')) FROM 'events.parquet'"))




