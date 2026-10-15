# quality_report.py — 주차 산출물 1: 데이터 품질 리포트
import pandas as pd


def profile(df: pd.DataFrame, name: str) -> pd.DataFrame:
    return pd.DataFrame({
        'dataset': name,
        'rows': [len(df)],
        'dup_order_id': [int(df['order_id'].duplicated().sum())],
        'null_price': [int(df['price'].isna().sum())],
        'null_rate_pct': [round(df['price'].isna().mean() * 100, 2)],
        'category_values': [df['category'].nunique()],
    })


raw = pd.read_csv('orders.csv')
cleaned = pd.read_parquet('orders_clean.parquet')

report = pd.concat([profile(raw, 'before'),
                    profile(cleaned, 'after')], ignore_index=True)
report.to_csv('quality_report.csv', index=False, encoding='utf-8')
print(report)
