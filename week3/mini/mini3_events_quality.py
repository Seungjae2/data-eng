# mini3_events_quality.py — 미니 과제 3: events.parquet(100만 행) 품질 측정, DuckDB SQL vs Pandas
# 사전 준비: week3 폴더에서 make_events.py → speed.py 를 실행해 events.parquet 가 있어야 함
from pathlib import Path
import time

import duckdb
import pandas as pd

HERE = Path(__file__).parent
DATA = HERE.parent
CLEAN = DATA / 'events.parquet'
DIRTY = HERE / 'events_dirty.parquet'
VALID_TYPES = ['view', 'cart', 'buy']


# 1단계 — 오염된 사본 (원본은 깨끗해서 지표가 모두 0). 랜덤 대신 event_id 규칙으로 골라 재현 가능
def make_dirty() -> None:
    duckdb.sql(f"""
        COPY (
            SELECT event_id, user_id, event_type,
                   CASE WHEN event_id % 1000 = 0 THEN NULL      -- 결측 1,000건
                        WHEN event_id % 5000 = 1 THEN -100      -- 음수 200건
                        ELSE value END AS value,
                   ts
            FROM '{CLEAN}'
            UNION ALL
            SELECT * FROM '{CLEAN}' WHERE event_id % 2000 = 7   -- 중복 500건
        ) TO '{DIRTY}' (FORMAT parquet, COMPRESSION zstd)
    """)


# 2단계 — 품질 측정을 전부 DuckDB SQL로
def profile_sql(path: Path) -> pd.DataFrame:
    types = ', '.join(f"'{t}'" for t in VALID_TYPES)
    return duckdb.sql(f"""
        SELECT count(*)                                          AS rows,
               count(*) - count(DISTINCT event_id)               AS dup_event_id,
               count(*) - count(value)                           AS null_value,
               count(DISTINCT event_type)                        AS type_values,
               count(*) FILTER (WHERE value <= 0)                AS value_le_0,
               count(*) FILTER (WHERE event_type NOT IN ({types})) AS unknown_type
        FROM '{path}'
    """).df()


# 3단계 — 같은 지표를 Pandas로 (파일 전체를 DataFrame으로 올린 뒤 계산)
def profile_pd(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path)
    return pd.DataFrame({
        'rows': [len(df)],
        'dup_event_id': [int(df['event_id'].duplicated().sum())],
        'null_value': [int(df['value'].isna().sum())],
        'type_values': [df['event_type'].nunique()],
        'value_le_0': [int((df['value'] <= 0).sum())],
        'unknown_type': [int((~df['event_type'].isin(VALID_TYPES)).sum())],
    })


def bench(fn, path: Path, rounds: int = 3):
    times = []
    for _ in range(rounds):
        t0 = time.perf_counter()
        result = fn(path)
        times.append(time.perf_counter() - t0)
    return result, sum(times) / len(times)


if __name__ == '__main__':
    make_dirty()

    rows = []
    for path in [CLEAN, DIRTY]:
        sql_res, sql_t = bench(profile_sql, path)
        pd_res, pd_t = bench(profile_pd, path)
        print(f'=== {path.name}')
        print(sql_res.to_string(index=False))
        print('두 방식 결과 일치:', sql_res.astype('int64').equals(pd_res.astype('int64')))
        print(f'DuckDB SQL: {sql_t:.3f}초 / Pandas: {pd_t:.3f}초 ({pd_t / sql_t:.1f}배)\n')
        rows.append({'dataset': path.name, **sql_res.iloc[0].to_dict(),
                     'duckdb_sec': round(sql_t, 3), 'pandas_sec': round(pd_t, 3)})

    pd.DataFrame(rows).to_csv(HERE / 'events_quality.csv', index=False, encoding='utf-8')

    # 4단계 — 메모리 비교
    df = pd.read_parquet(CLEAN)
    print(f'Pandas DataFrame 메모리: {df.memory_usage(deep=True).sum() / 1024 / 1024:,.0f} MB')
    print(f'DuckDB 결과 메모리     : {profile_sql(CLEAN).memory_usage(deep=True).sum():,} bytes')
