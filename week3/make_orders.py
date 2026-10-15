import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 1000

orders = pd.DataFrame({
	'order_id': np.arange(1, n + 1),
	'customer_id': rng.integers(1, 201, n),
	'category': rng.choice(['식품', '가전', '의류', '도서'], n, p=[0.4, 0.2, 0.3, 0.1]),
	'price': rng.integers(1, 200, n) * 1000,
	'quantity': rng.integers(1, 6, n),
	'order_date': pd.to_datetime('2026-06-01')
		+ pd.to_timedelta(rng.integers(0, 60, n), unit='D'),
})

# 품질 문제를 일부러 심는다 - 3-5 품질 리포트의 재료가 된다.
orders.loc[rng.choice(n, 30, replace=False), 'price'] = np.nan
orders.loc[rng.choice(n, 20, replace=False), 'category'] = ' 식품 '
orders = pd.concat([orders, orders.sample(15, random_state=42)])
orders['order_date'] = orders['order_date'].astype(str)

orders.to_csv('orders.csv', index=False, encoding='utf-8')
print(len(orders), '행 저장 완료')
