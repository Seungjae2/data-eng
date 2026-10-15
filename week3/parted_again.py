import duckdb

duckdb.sql("""
	COPY (SELECT * FROM 'events.csv')
	TO 'events_parted'
	(FORMAT parquet, PARTITION_BY (event_type), COMPRESSION zstd)
""")

