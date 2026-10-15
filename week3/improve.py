# improve.py — 2단계 단독 파일
import pandas as pd

rep = pd.read_csv('quality_report.csv')
before = rep[rep['dataset'] == 'before'].iloc[0]
after = rep[rep['dataset'] == 'after'].iloc[0]

print('중복 제거:', before['dup_order_id'], '->', after['dup_order_id'], '건')
print('결측 보정:', before['null_price'], '->', after['null_price'], '건')
print('카테고리 표기 통일:', before['category_values'], '->', after['category_values'], '가지')
print('행 수 변화:', before['rows'], '->', after['rows'],
      f"({(after['rows'] - before['rows']) / before['rows'] * 100:.1f}%)")

