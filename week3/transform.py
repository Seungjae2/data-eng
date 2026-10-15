# transform.py — 1~8단계를 이 파일에 이어 붙입니다
import pandas as pd
df = pd.read_csv('orders.csv')

# 열 하나 → Series
print(type(df['price']))

# 열 여러 개 → DataFrame (대괄호가 두 겹인 것에 주의)
print(type(df[['order_id', 'price']]))

# 위치로 — iloc (끝 제외)
print(df.iloc[0:3])

# 이름표로 — loc (끝 포함)
print(df.loc[0:2])

# 2단계 — transform.py 끝에 이어 붙입니다
# 조건 필터 — 불리언 인덱싱
food = df[df['category'].str.strip() == '식품']
big = df[(df['price'] >= 100000) & (df['quantity'] >= 3)]
print('식품 주문:', len(food), '건 / 고액·다수량:', len(big), '건')

# loc — 행 조건과 열 목록을 한 번에
sub = df.loc[df['customer_id'].isin([1, 2, 3]),
             ['order_id', 'customer_id', 'price']]
print(sub.head(3))

# 2단계(일부러 실패) — transform.py 끝에 이어 붙입니다
# strip을 빼면 몇 건이 새는지 확인해 봅니다
without_strip = df[df['category'] == '식품']
with_strip = df[df['category'].str.strip() == '식품']
print('strip 없이:', len(without_strip))
print('strip 하고:', len(with_strip))
print('놓친 건수 :', len(with_strip) - len(without_strip))

# 3단계 — transform.py 끝에 이어 붙입니다
# 어떤 값들이 들어 있나
print(df['category'].unique())
print(df['category'].nunique(), '가지')

# 각각 몇 건인가 — 오염이 눈에 보입니다
print(df['category'].value_counts())

# 4단계 — transform.py 끝에 이어 붙입니다
df['category'] = df['category'].str.strip()
df['order_date'] = pd.to_datetime(df['order_date'])
df = df.assign(amount=df['price'] * df['quantity'])

print(df.dtypes)
print('6월 첫 주 주문:', len(df[df['order_date'] < '2026-06-08']), '건')
print('카테고리:', df['category'].nunique(), '가지')


# 5단계 — transform.py 끝에 이어 붙입니다
# datetime이 되고 나면 .dt로 부품을 꺼낼 수 있습니다
df['year'] = df['order_date'].dt.year
df['month'] = df['order_date'].dt.month
df['weekday'] = df['order_date'].dt.day_name()

print(df[['order_date', 'year', 'month', 'weekday']].head(3))
print(df['weekday'].value_counts())

# 6단계 — transform.py 끝에 이어 붙입니다
print('결측 현황:')
print(df.isna().sum())

# 방법 1 — 결측 행을 버린다
print('버리면:', len(df.dropna(subset=['price'])), '행')

# 방법 2 — 대표값으로 채운다
filled = df['price'].fillna(df['price'].median())
print('중앙값으로 채우면 결측:', filled.isna().sum())

# 방법 3 — 그대로 두고 집계에서 제외 (Pandas 기본 동작)
print('평균(결측 자동 제외):', round(df['price'].mean()))

# 7단계 — transform.py 끝에 이어 붙입니다
df.to_parquet('orders_step1.parquet', index=False)

check = pd.read_parquet('orders_step1.parquet')
print('CSV로 읽은 날짜 타입   :', pd.read_csv('orders.csv')['order_date'].dtype)
print('Parquet로 읽은 날짜 타입:', check['order_date'].dtype)
print('저장된 열:', check.columns.tolist())


for cat in df['category'].unique():
    sub = df[df['category'] == cat]
    print(cat, round(sub['amount'].mean()))
 
print(df[df['quantity'] == 5][['order_id', 'amount']].head())
print(df.sort_values('amount', ascending=False).head(10)[['order_id', 'category', 'amount']])
