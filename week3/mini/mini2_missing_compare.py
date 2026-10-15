# mini2_missing_compare.py — 미니 과제 2: 결측 처리 방식 비교 (중앙값 보정 vs 행 버리기)
from pathlib import Path

import duckdb
import pandas as pd

from mini1_range_check import profile

HERE = Path(__file__).parent
DATA = HERE.parent


def load_raw() -> pd.DataFrame:
    return duckdb.sql(f"SELECT * FROM '{DATA / 'orders.csv'}'").df()


def base_clean(df: pd.DataFrame) -> pd.DataFrame:
    """결측 처리 직전까지 — 두 방식이 공통으로 거치는 단계 (순서: 공백 → 날짜 → 중복)"""
    out = df.copy()
    out['category'] = out['category'].str.strip()
    out['order_date'] = pd.to_datetime(out['order_date'])
    out = out.drop_duplicates(subset='order_id', keep='first')
    return out


def stats(df: pd.DataFrame, name: str) -> pd.DataFrame:
    amount = df['price'] * df['quantity']
    return pd.DataFrame({
        'method': name,
        'rows': [len(df)],
        'price_mean': [round(df['price'].mean())],
        'price_median': [df['price'].median()],
        'price_std': [round(df['price'].std())],
        'amount_sum': [int(amount.sum())],
    })


if __name__ == '__main__':
    raw = load_raw()
    base = base_clean(raw)

    # 방식 A — 중앙값 보정 (기존 clean_orders.py 방식)
    median_df = base.copy()
    median_df['price'] = median_df['price'].fillna(median_df['price'].median())

    # 방식 B — 결측 행 버리기
    drop_df = base.dropna(subset=['price'])

    # 1) 품질 리포트를 두 방식으로 다시 냄
    report = pd.concat([profile(raw, 'before'),
                        profile(median_df, 'after_median'),
                        profile(drop_df, 'after_dropna')], ignore_index=True)
    report.to_csv(HERE / 'quality_report_dropna.csv', index=False, encoding='utf-8')
    print(report.to_string(), '\n')

    # 2) 두 방식의 통계 비교
    cmp = (pd.concat([stats(median_df, 'median'), stats(drop_df, 'dropna')],
                     ignore_index=True)
           .set_index('method').T)
    cmp['diff'] = cmp['median'] - cmp['dropna']
    cmp['diff_pct'] = (cmp['diff'] / cmp['dropna'] * 100).round(2)
    print(cmp.to_string())
