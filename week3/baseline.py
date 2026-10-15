import duckdb

baseline = duckdb.sql("""
	SELECT 	count(*)				AS rows,
		count(*) - count(price)			AS null_price,
		count(*) - count(DISTINCT order_id)	AS dub_orders,
		count(DISTINCT category)		AS category_values
	FROM 	'orders.csv'
""").df()
print(baseline)

# 1단계(오염 확인) — baseline.py 끝에 이어 붙입니다
# 어떤 값이 오염됐는지 눈으로 확인
print(duckdb.sql("""
    SELECT category, count(*) AS cnt
    FROM 'orders.csv'
    GROUP BY category
    ORDER BY cnt DESC
"""))



