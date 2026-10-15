# explore.py — 3~6단계를 이 파일에 이어 붙입니다
import pandas as pd

df = pd.read_csv('orders.csv')

print(df.shape)          # (행, 열)
print(df.dtypes)         # 열마다 타입
print(df.head(3))        # 앞 3줄
df.info()                # 결측 수까지 한눈에 (print 로 감싸면 끝에 None 이 한 줄 더 찍힙니다)
print(df.describe())     # 숫자 열의 기초 통계

# 4단계 — explore.py 끝에 이어 붙입니다
# price는 정수만 넣었는데 float64입니다
print('price dtype :', df['price'].dtype)
print('quantity dtype:', df['quantity'].dtype)

# 이유는 결측(NaN) 때문입니다
print('price 결측 :', df['price'].isna().sum())
print('quantity 결측:', df['quantity'].isna().sum())

# 값 몇 개를 보면 1000이 1000.0으로 보입니다
print(df['price'].head(3).tolist())

# 5단계 — explore.py 끝에 이어 붙입니다
df.to_parquet('orders_raw.parquet', index=False)

import os
csv_size = os.path.getsize('orders.csv')
pq_size = os.path.getsize('orders_raw.parquet')
print(f'CSV    : {csv_size:,} bytes')
print(f'Parquet: {pq_size:,} bytes  ({pq_size / csv_size:.0%})')

# 6단계 — explore.py 끝에 이어 붙입니다
# Parquet — 두 열만 읽습니다
slim = pd.read_parquet('orders_raw.parquet', columns=['category', 'price'])
print(slim.shape)
print(slim.columns.tolist())

# CSV — usecols로 지정해도 파일 전체는 읽어야 합니다
slim_csv = pd.read_csv('orders.csv', usecols=['category', 'price'])
print(slim_csv.shape)
