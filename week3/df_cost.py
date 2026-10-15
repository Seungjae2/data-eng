# df_cost.py — 5단계 단독 파일(100만 행을 통째로 올리니 roundtrip.py 에 붙이지 않습니다)
import time
import duckdb

# 나쁜 예 — 100만 행을 통째로 DataFrame으로
t0 = time.perf_counter()
big = duckdb.sql("SELECT * FROM 'events.parquet'").df()
t1 = time.perf_counter()
print(f'전체 변환  : {t1-t0:.2f}초, {big.memory_usage(deep=True).sum()/1024/1024:,.0f} MB, {len(big):,}행')

# 좋은 예 — 줄인 다음에
t0 = time.perf_counter()
small = duckdb.sql("SELECT event_type, sum(value) AS v FROM 'events.parquet' GROUP BY event_type").df()
t1 = time.perf_counter()
print(f'집계 후 변환: {t1-t0:.2f}초, {small.memory_usage(deep=True).sum():,} bytes, {len(small)}행')

del big
