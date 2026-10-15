# first_buy.py
import duckdb

print(duckdb.sql("""
    WITH first_buy AS (
        SELECT user_id,
               min(ts) FILTER (WHERE event_type = 'buy') AS first_buy_ts
        FROM 'events.parquet'
        GROUP BY user_id
    )
    SELECT date_trunc('week', first_buy_ts) AS cohort_week,
           count(*) AS users
    FROM first_buy
    WHERE first_buy_ts IS NOT NULL
    GROUP BY cohort_week
    ORDER BY cohort_week
"""))
