import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 1_000_000

events = pd.DataFrame({
	'event_id' : np.arange(n),
	'user_id' : rng.integers(1, 50_001, n),
	'event_type' : rng.choice(['view', 'cart', 'buy'], n, p=[0.8, 0.15, 0.05]),
	'value' : rng.integers(1, 100, n) * 100,
	'ts' : pd.to_datetime('2026-06-01')
	     + pd.to_timedelta(rng.integers(0, 60 * 24 * 3600, n), unit='s'),
})
events.to_csv('events.csv', index=False)
print('생성 완료:', len(events), '행')
