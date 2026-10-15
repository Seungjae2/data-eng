import os
import time
import duckdb

duckdb.sql("""
	COPY (SELECT * FROM 'events.csv')
	TO 'events.parquet' (FORMAT parquet, COMPRESSION zstd)
""")
print('Convert Suceed')

#2
csv = os.path.getsize('events.csv')
pq = os.path.getsize('events.parquet')
print(f'CSV	: {csv/1024/1024:,.1f} MB')
print(f'Parquet : {pq/1024/1024:,.1f} MB')
print(f'비율	: {pq/csv:.1%} ({csv/pq:.1f}배 작아짐)')


# 3단계 — speed.py 끝에 이어 붙입니다
def bench(sql, rounds=3):
    times = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        duckdb.sql(sql).fetchall()
        times.append(time.perf_counter() - t0)
    return sum(times) / len(times)

csv_t = bench("SELECT event_type, sum(value) FROM 'events.csv' GROUP BY event_type")
pq_t  = bench("SELECT event_type, sum(value) FROM 'events.parquet' GROUP BY event_type")

print(f'CSV     질의: {csv_t:.3f} 초')
print(f'Parquet 질의: {pq_t:.3f} 초')
print(f'차이        : {csv_t/pq_t:.1f}배')


# 4단계 — speed.py 끝에 이어 붙입니다
# 먼저 일부러 틀린 비교 — 「전부 읽기」를 count(*) 로 잽니다
one_col = bench("SELECT sum(value) FROM 'events.parquet'")
all_cnt = bench("SELECT count(*) FROM (SELECT * FROM 'events.parquet')")
print(f'한 열만            : {one_col:.4f} 초')
print(f'전부 읽기(count(*)): {all_cnt:.4f} 초')

# 다섯 열을 정말로 읽게 합니다 — 열마다 집계를 하나씩
five = "SELECT max(event_id), max(user_id), max(event_type), sum(value), max(ts) FROM "
all_col = bench(five + "'events.parquet'")
print(f'다섯 열 전부       : {all_col:.4f} 초  (한 열의 {all_col/one_col:.1f}배)')

# CSV는 어느 쪽이든 전체를 파싱해야 합니다
csv_one = bench("SELECT sum(value) FROM 'events.csv'")
csv_all = bench(five + "'events.csv'")
print(f'\nCSV 한 열만  : {csv_one:.3f} 초')
print(f'CSV 다섯 열  : {csv_all:.3f} 초')

# 5단계 — speed.py 끝에 이어 붙입니다
for comp in ['zstd', 'snappy', 'gzip']:
    out = f'events_{comp}.parquet'
    duckdb.sql(f"COPY (SELECT * FROM 'events.csv') TO '{out}' (FORMAT parquet, COMPRESSION {comp})")
    size = os.path.getsize(out) / 1024 / 1024
    t = bench(f"SELECT event_type, sum(value) FROM '{out}' GROUP BY event_type")
    print(f'{comp:8s}  {size:6.1f} MB   {t:.3f} 초')

# 6단계 — speed.py 끝에 이어 붙입니다
duckdb.sql("""
    COPY (SELECT *, CAST(ts AS DATE) AS day FROM 'events.csv')
    TO 'events_parted'
    (FORMAT parquet, PARTITION_BY (event_type), COMPRESSION zstd, OVERWRITE_OR_IGNORE)
""")
print('파티션 저장 완료')

parted = bench("SELECT sum(value) FROM 'events_parted/*/*.parquet' WHERE event_type = 'buy'")
single = bench("SELECT sum(value) FROM 'events.parquet' WHERE event_type = 'buy'")
print(f'파티션됨 : {parted:.4f} 초')
print(f'단일 파일: {single:.4f} 초')
