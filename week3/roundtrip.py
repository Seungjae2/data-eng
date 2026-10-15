# roundtrip.py — 1~4단계를 이 파일에 이어 붙입니다
import duckdb
import pandas as pd

top = duckdb.sql("""
    SELECT user_id, sum(value) AS spend
    FROM 'events.parquet'
    WHERE event_type = 'buy'
    GROUP BY user_id
    ORDER BY spend DESC
    LIMIT 100
""").df()

print(type(top), top.shape)
print('spend 범위:', top['spend'].min(), '~', top['spend'].max())

# 일부러 실패 — 경계를 눈대중으로 정하면?
top['grade'] = pd.cut(top['spend'],
                      bins=[0, 15000, 25000, float('inf')],
                      labels=['B', 'A', 'S'])
print(top['grade'].value_counts())

# 1단계(분위수 경계) — roundtrip.py 끝에 이어 붙입니다
q = top['spend'].quantile([0.33, 0.66]).tolist()
print('경계값 후보:', [round(x) for x in q])

top['grade2'] = pd.cut(top['spend'],
                       bins=[0, q[0], q[1], float('inf')],
                       labels=['B', 'A', 'S'])
print(top['grade2'].value_counts())

# 2단계 — roundtrip.py 끝에 이어 붙입니다. DataFrame을 SQL로
grade_summary = duckdb.sql("""
    SELECT grade2 AS grade, count(*) AS users, avg(spend) AS avg_spend
    FROM top
    GROUP BY grade2
    ORDER BY avg_spend DESC
""").df()
print(grade_summary)


# 3단계 — roundtrip.py 끝에 이어 붙입니다
# ① SQL — 100만 행에서 사용자별 요약으로 줄인다
users = duckdb.sql("""
    SELECT user_id,
           count(*) FILTER (WHERE event_type = 'view') AS views,
           count(*) FILTER (WHERE event_type = 'cart') AS carts,
           count(*) FILTER (WHERE event_type = 'buy')  AS buys,
           sum(value) FILTER (WHERE event_type = 'buy') AS spend
    FROM 'events.parquet'
    GROUP BY user_id
""").df()
print('① SQL 집계 후:', users.shape)

# ② Pandas — 전환율 계산과 라벨링 (세밀한 규칙)
users['cvr'] = (users['buys'] / users['views']).fillna(0).round(3)
users['segment'] = 'normal'
users.loc[users['cvr'] >= 0.1, 'segment'] = 'high_intent'
users.loc[users['buys'] == 0, 'segment'] = 'browser'
print('② Pandas 가공 후:', users.shape)

# ③ SQL — 세그먼트별 요약
seg = duckdb.sql("""
    SELECT segment,
           count(*) AS users,
           round(avg(cvr), 3) AS avg_cvr,
           round(avg(coalesce(spend, 0))) AS avg_spend
    FROM users
    GROUP BY segment
    ORDER BY users DESC
""").df()
print('③ 세그먼트 요약')
print(seg)

# 4단계 — roundtrip.py 끝에 이어 붙입니다
import os

# Pandas로 저장
users.to_parquet('user_segments.parquet', index=False)

# DuckDB로 저장 (DataFrame을 그대로 COPY)
duckdb.sql("COPY (SELECT * FROM seg) TO 'segment_summary.parquet' (FORMAT parquet)")

for f in ['user_segments.parquet', 'segment_summary.parquet']:
    print(f, f'{os.path.getsize(f)/1024:.1f} KB')







