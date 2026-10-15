# crosstab.py
import duckdb

print(duckdb.sql("""
    PIVOT 'orders_enriched.parquet'
    ON category
    USING sum(amount)
    GROUP BY region
    ORDER BY region
"""))
