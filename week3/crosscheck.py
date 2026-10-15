# crosscheck.py — 3단계 단독 파일
import duckdb

print(duckdb.sql("""
    SELECT count(*)                            AS rows,
           count(*) - count(price)             AS null_price,
           count(*) - count(DISTINCT order_id) AS dup_orders,
           count(DISTINCT category)            AS category_values,
           min(order_date)                     AS first_date,
           max(order_date)                     AS last_date
    FROM 'orders_clean.parquet'
"""))


