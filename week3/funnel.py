# funnel.py — 6단계 정답 예시(퍼널) 단독 파일
import duckdb

print(duckdb.sql("""
    WITH per_user AS (
        SELECT user_id,
               max(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) AS viewed,
               max(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS carted,
               max(CASE WHEN event_type = 'buy'  THEN 1 ELSE 0 END) AS bought
        FROM 'events.parquet'
        GROUP BY user_id
    )
    SELECT sum(viewed) AS viewed,
           sum(carted) AS carted,
           sum(bought) AS bought,
           round(sum(carted) * 100.0 / sum(viewed), 1) AS view_to_cart,
           round(sum(bought) * 100.0 / sum(carted), 1) AS cart_to_buy
    FROM per_user
"""))
