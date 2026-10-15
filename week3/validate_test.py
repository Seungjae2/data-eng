# validate_test.py — 5단계 두 블록을 이 파일에 이어 붙입니다
import pandas as pd

def validate(df: pd.DataFrame) -> dict:
    today = pd.Timestamp.today()          # 실행하는 날 — 이보다 뒤 주문은 있을 수 없다
    return {
        'price_le_0':    int((df['price'] <= 0).sum()),
        'quantity_le_0': int((df['quantity'] <= 0).sum()),
        'future_date':   int((df['order_date'] > today).sum()),
        'unknown_cat':   int((~df['category'].isin(['식품', '가전', '의류', '도서'])).sum()),
    }

cleaned = pd.read_parquet('orders_clean.parquet')
print(validate(cleaned))

# 5단계(검사기 깨뜨리기) — validate_test.py 끝에 이어 붙입니다
# 일부러 나쁜 값을 넣어 검사기가 실제로 잡는지 확인합니다
bad = cleaned.copy()
bad.loc[0, 'price'] = -1000
bad.loc[1, 'category'] = '알수없음'
print(validate(bad))



