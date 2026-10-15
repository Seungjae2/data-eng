# 3-5 미니 과제 — 범위 점검 · 결측 처리 비교 · 100만 행 품질 측정

대표 산출물([../quality_report.md](../quality_report.md))과 섞이지 않도록 이 폴더에 따로 둠. 원본 데이터는 상위 `week3/`의 것을 그대로 읽음

| 과제 | 파일 | 결과 파일 |
|---|---|---|
| 1. 값 범위 점검을 `profile()`에 추가 | [mini1_range_check.py](mini1_range_check.py) | [quality_report_range.csv](quality_report_range.csv) |
| 2. 결측 처리 — 중앙값 보정 vs 행 버리기 | [mini2_missing_compare.py](mini2_missing_compare.py) | [quality_report_dropna.csv](quality_report_dropna.csv) |
| 3. events 100만 행 품질 측정 — DuckDB SQL vs Pandas | [mini3_events_quality.py](mini3_events_quality.py) | [events_quality.csv](events_quality.csv) |

## 1. 값 범위 점검

`profile()`에 두 열을 추가함

- `price_le_0`: 가격 0 이하
- `qty_out_of_range`: 수량 1 미만 또는 6 이상 (`make_orders.py`가 1~5로 생성하므로 6부터는 있을 수 없는 값)

| dataset | rows | dup_order_id | null_price | category_values | price_le_0 | qty_out_of_range |
|---|---|---|---|---|---|---|
| before | 1,015 | 15 | 30 | 5 | 0 | 0 |
| after | 1,000 | 0 | 0 | 4 | 0 | 0 |
| injected | 1,000 | 0 | 0 | 4 | **3** | **2** |

원본에는 범위 위반이 원래 없어서 before·after 모두 0 → 0만으로는 검사가 동작하는지 알 수 없음. 그래서 정제 결과에 나쁜 값(가격 0 · -500 · -1000, 수량 0 · 7)을 일부러 심은 `injected` 행을 추가했고, 심은 5건이 정확히 잡힘

## 2. 결측 처리 방식 비교

공백 제거 → 날짜 변환 → 중복 제거까지는 `base_clean()`으로 공통 처리하고, 결측 처리 한 줄만 다르게 해서 비교

| 지표 | 중앙값 보정 | 행 버리기 | 차이 |
|---|---|---|---|
| 행 수 | 1,000 | 970 | 30건 (3.09%) |
| price 평균 | 100,420 | 100,418 | 2원 (0.00%) |
| price 중앙값 | 100,500 | 100,500 | 0 |
| price 표준편차 | 56,077 | 56,939 | -862 (-1.51%) |
| **매출 합계** | **291,021,500** | **283,283,000** | **7,738,500 (2.73%)** |

- **대표값(평균·중앙값)은 거의 같음**: 결측이 무작위로 3% 수준이라 어느 방식이든 분포의 중심이 거의 그대로임
- **합계 지표는 2.73% 차이**: 행을 버리면 주문 30건이 통째로 사라져 매출이 과소 집계됨
- **표준편차는 보정 쪽이 작음**: 30건을 모두 같은 값(중앙값)으로 채워 분포가 가운데로 몰림 → 실제보다 변동이 작아 보이는 부작용
- **결론**: 매출·건수처럼 더하는 지표가 중요하면 보정, 값의 분포를 분석하려면 행 버리기가 적합함. 어느 쪽이든 리포트에 처리 방식을 명시해야 함

## 3. events 100만 행 품질 측정 — DuckDB SQL vs Pandas

orders와 같은 구조(행 수 · 중복 · 결측 · 고유값 · 범위 · 미지 값)를 DuckDB SQL로만 측정하고, 같은 지표를 Pandas로도 계산해 비교

| 지표 | Pandas | DuckDB SQL |
|---|---|---|
| 중복 | `duplicated().sum()` | `count(*) - count(DISTINCT event_id)` |
| 결측 | `isna().sum()` | `count(*) - count(value)` — `count(열)`은 NULL을 빼고 셈 |
| 범위 위반 | `(df['value'] <= 0).sum()` | `count(*) FILTER (WHERE value <= 0)` |
| 미지 값 | `~isin([...])` | `NOT IN (...)` |

원본 `events.parquet`는 깨끗해서 지표가 모두 0이라, DuckDB로 오염 사본(`events_dirty.parquet`)을 만들어 함께 측정함. 랜덤 대신 `event_id % 1000 = 0` 같은 규칙으로 골라 몇 번을 돌려도 같은 결과가 나옴

| dataset | rows | dup_event_id | null_value | value_le_0 | unknown_type | DuckDB | Pandas |
|---|---|---|---|---|---|---|---|
| events.parquet | 1,000,000 | 0 | 0 | 0 | 0 | 0.023초 | 0.057초 |
| events_dirty.parquet | 1,000,500 | **500** | **1,000** | **200** | 0 | 0.023초 | 0.048초 |

- 심은 오염(중복 500 · 결측 1,000 · 음수 200)을 정확히 잡았고, 두 방식의 결과가 모두 일치함
- 속도는 DuckDB가 약 2배 빠름. 3-3의 47배만큼 벌어지지 않는 이유는 ① 이번엔 둘 다 Parquet을 읽어 Pandas도 빠르고 ② 중복을 세는 `count(DISTINCT)`가 DuckDB에서도 무거운 연산이기 때문
- **진짜 차이는 메모리**: Pandas는 측정하려고 100만 행 전체(89 MB)를 메모리에 올리지만, DuckDB는 파일에서 바로 집계해 결과 한 줄(176 bytes)만 돌려줌 → 데이터가 메모리보다 커지면 Pandas 방식은 아예 불가능

## 실행 방법

상위 `week3/`에 `orders_clean.parquet`와 `events.parquet`가 있어야 함 (`clean_orders.py`, `make_events.py` → `speed.py`로 생성)

```bash
cd week3/mini
python3 mini1_range_check.py
python3 mini2_missing_compare.py
python3 mini3_events_quality.py   # events_dirty.parquet 생성 후 측정 (parquet은 .gitignore로 제외)
```

측정 시간은 실행 환경에 따라 달라짐
