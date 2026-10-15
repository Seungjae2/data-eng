# make_customers.py — 고객 마스터 생성 (시드 고정)
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
customers = pd.DataFrame({
    'customer_id': np.arange(1, 201),
    'region': rng.choice(['서울', '경기', '부산', '광주'], 200),
    'joined': pd.to_datetime('2025-01-01')
        + pd.to_timedelta(rng.integers(0, 365, 200), unit='D'),
})
customers.to_csv('customers.csv', index=False, encoding='utf-8')

df = pd.read_parquet('orders_step1.parquet')
print('orders:', df.shape, '/ customers:', customers.shape)
