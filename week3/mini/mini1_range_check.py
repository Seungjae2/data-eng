# mini1_range_check.py — 미니 과제 1: 값 범위 점검을 profile()에 추가
# 대표 산출물(../quality_report.py)은 그대로 두고, 범위 점검을 더한 버전을 따로 만든다.
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent      # week3/mini
DATA = HERE.parent                # week3


def profile(df: pd.DataFrame, name: str) -> pd.DataFrame:
    return pd.DataFrame({
        'dataset': name,
        'rows': [len(df)],
        'dup_order_id': [int(df['order_id'].duplicated().sum())],
        'null_price': [int(df['price'].isna().sum())],
        'null_rate_pct': [round(df['price'].isna().mean() * 100, 2)],
        'category_values': [df['category'].nunique()],
        # 추가 — 값 범위 점검 (수량은 make_orders.py가 1~5로 생성하므로 6 이상은 위반)
        'price_le_0': [int((df['price'] <= 0).sum())],
        'qty_out_of_range': [int(((df['quantity'] < 1) | (df['quantity'] >= 6)).sum())],
    })


if __name__ == '__main__':
    raw = pd.read_csv(DATA / 'orders.csv')
    cleaned = pd.read_parquet(DATA / 'orders_clean.parquet')

    # 원본에는 범위 위반이 없어 0만 나오므로, 검사가 실제로 잡는지 보려고 나쁜 값을 심은 사본
    injected = cleaned.copy()
    injected.loc[0:2, 'price'] = [0, -500, -1000]   # 가격 0 이하 3건
    injected.loc[3:4, 'quantity'] = [0, 7]          # 수량 범위 밖 2건

    report = pd.concat([profile(raw, 'before'),
                        profile(cleaned, 'after'),
                        profile(injected, 'injected')], ignore_index=True)
    report.to_csv(HERE / 'quality_report_range.csv', index=False, encoding='utf-8')
    print(report.to_string())
