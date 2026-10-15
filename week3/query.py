# query.py — 3~6단계를 이 파일에 이어 붙입니다
import duckdb
import pandas as pd

print(duckdb.sql("""
    SELECT event_type, count(*) AS cnt, sum(value) AS total
    FROM 'events.csv'
    GROUP BY event_type
    ORDER BY cnt DESC
""")

)


# 4단계 — query.py 끝에 이어 붙입니다
# 어떤 열이 있고 타입이 무엇인지
print(duckdb.sql("DESCRIBE SELECT * FROM 'events.csv'"))

# 앞 몇 줄만
print(duckdb.sql("SELECT * FROM 'events.csv' LIMIT 5"))

# 행 수
print(duckdb.sql("SELECT count(*) FROM 'events.csv'"))

# 5단계 — query.py 끝에 이어 붙입니다
# 조건 필터
print(duckdb.sql("""
    SELECT count(*) FROM 'events.csv' WHERE event_type = 'buy'
"""))

# 2-2에서 배운 문법이 그대로 통합니다
print(duckdb.sql("""
    WITH daily AS (
        SELECT date_trunc('day', ts) AS d,
               event_type,
               sum(value) AS total
        FROM 'events.csv'
        GROUP BY 1, 2
    )
    SELECT d, event_type, total,
           sum(total) OVER (PARTITION BY event_type ORDER BY d) AS running
    FROM daily
    ORDER BY event_type, d
    LIMIT 6
"""))

# 6단계 — query.py 끝에 이어 붙입니다
df = duckdb.sql("""
    SELECT event_type, count(*) AS cnt, avg(value) AS avg_value
    FROM 'events.csv'
    GROUP BY event_type
    ORDER BY cnt DESC
""").df()          # ← .df()가 DataFrame으로 변환합니다

print(type(df))
print(df)
print(df.dtypes)

# 6단계(반대 방향) — query.py 끝에 이어 붙입니다. DataFrame을 SQL에서 바로 참조
orders = pd.read_parquet('orders_enriched.parquet')

print(duckdb.sql("""
    SELECT region, count(*) AS cnt, sum(amount) AS total
    FROM orders            -- 파이썬 변수 이름을 그대로 씁니다
    GROUP BY region
    ORDER BY total DESC
"""))



