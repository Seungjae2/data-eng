# 3주차 산출물 — 주문 데이터 품질 파이프라인 + CSV→Parquet 성능 실측

## 1. 데이터 품질 리포트 (대표 산출물)

- 파일: [quality_report.md](quality_report.md) (전후 지표 · 처리 근거 · 검증) / 수치 원본 [quality_report.csv](quality_report.csv)
- 파이프라인: [clean_orders.py](clean_orders.py) — DuckDB로 추출 → Pandas로 정제 → 검증 통과 시에만 Parquet 저장
- 원본 `orders.csv`는 [make_orders.py](make_orders.py)가 시드를 고정해 만들고, 품질 문제를 일부러 심음 (결측 30 · 공백 오염 20 · 중복 15)

| 지표 | before | after |
|---|---|---|
| 행 수 | 1,015 | 1,000 |
| order_id 중복 | 15 | 0 |
| price 결측 | 30 (2.96%) | 0 |
| category 고유값 | 5 (`' 식품 '` 포함) | 4 |

처리 순서가 결과를 바꾼다는 것도 확인함: 중복을 먼저 지우고 중앙값을 구하면 100,500, 중복이 있는 채로 구하면 101,000 → **중복 제거 → 결측 보정** 순서로 고정 ([order_test.py](order_test.py))

검증에 실패하면 파일을 쓰지 않고 종료 코드 1로 끝냄 — 다음 단계가 오염된 데이터를 받지 않게 하려는 장치

```python
if any(v > 0 for v in issues.values()):
    print('검증 실패:', issues)
    raise SystemExit(1)
```

## 2. CSV vs Parquet 성능 실측

- 파일: [실측기록_3-3.md](실측기록_3-3.md) · 측정 코드 [speed.py](speed.py)
- 대상: 이벤트 로그 100만 행 ([make_events.py](make_events.py), 5개 열)

| 항목 | CSV | Parquet(zstd) | 차이 |
|---|---|---|---|
| 파일 크기 | 40.6 MB | 9.8 MB | 4.1배 작음 |
| 집계 질의 | 0.063초 | 0.001초 | 47.3배 빠름 |
| 한 열만 읽기 | 0.060초 | 0.0006초 | — |
| 다섯 열 읽기 | 0.067초 | 0.0048초 | — |

- 압축 방식 비교: zstd 9.8 MB · gzip 10.6 MB · snappy 15.9 MB → zstd 채택
- `event_type` 기준 파티션 저장(`events_parted/event_type=buy/…`)도 실습
- 측정 함정: `count(*)`로 「전부 읽기」를 재면 오히려 빠르게 나옴 — DuckDB가 열을 읽지 않고 Parquet 메타데이터의 행 수만 가져오기 때문. 열마다 집계를 걸어 실제로 읽게 해서 다시 측정함

## 3. 분석 실습 결과 (DuckDB SQL + Pandas)

| 분석 | 결과 | 파일 |
|---|---|---|
| 퍼널 (사용자 5만 명) | 조회 50,000 → 장바구니 47,525 (95.1%) → 구매 31,501 (66.3%) | [funnel.py](funnel.py) |
| 첫 구매 주차 코호트 | 6/1 주 5,522명 → 7/20 주 2,425명으로 감소 | [first_buy.py](first_buy.py) |
| 사용자 세그먼트 | browser 18,499 · normal 18,015 (평균 CVR 0.065) · high_intent 13,486 (0.162) | [roundtrip.py](roundtrip.py) |
| 지역별 매출 SQL ↔ Pandas 대조 | 4개 지역 모두 차이 0 | [sql_analysis.py](sql_analysis.py) |

**SQL로 줄이고 Pandas로 다듬기**: 100만 행을 통째로 DataFrame으로 만들면 0.63초 · 42 MB, SQL로 먼저 집계하면 0.01초 · 191 bytes ([df_cost.py](df_cost.py)). 그래서 roundtrip.py는 ① SQL 집계(100만 → 5만 행) ② Pandas 라벨링 ③ SQL 요약 순으로 짬

## 4. 일부러 실패시켜 본 것

| 시도 | 결과 | 배운 점 |
|---|---|---|
| `strip()` 없이 `'식품'` 필터 | 416건 중 20건 누락 | 공백 오염은 눈에 안 보여 집계가 조용히 틀림 |
| 중복 있는 고객 마스터와 `merge` | 1,015 → 1,040행, 매출 2억 8,799만 → 2억 9,726만 | `validate='many_to_one'`을 주면 `MergeError`로 차단됨 |
| 윈도 함수 결과를 `WHERE`로 거르기 | `Binder Error` | `QUALIFY` 또는 CTE로 한 겹 감싸서 해결 |
| 검사기에 일부러 나쁜 값 주입 | 음수 가격 1 · 미지 카테고리 1 검출 | 검사기 자체도 검증해야 함 |
| 날짜 인덱스 없이 `resample` | `TypeError` | `set_index('order_date')` 후 사용 |

## 5. 파일 구성

| 일차 | 주제 | 파일 |
|---|---|---|
| 3-1 | Pandas 탐색·변환 | make_orders · explore · transform |
| 3-2 | 집계·결합·시계열 | make_customers · analyze · timeseries |
| 3-3 | DuckDB · Parquet | make_events · query · speed · parted_again |
| 3-4 | SQL 분석 · SQL↔Pandas 왕복 | sql_analysis · roundtrip · df_cost · funnel · first_buy · crosstab |
| 3-5 | 품질 파이프라인 | baseline · clean_orders · check_rerun · order_test · validate_test · crosscheck · quality_report · improve |

스크립트가 같은 폴더의 파일을 상대 경로로 읽으므로 일차별 하위 폴더로 나누지 않음

## 6. 실행 방법

```bash
cd week3
python3 -m venv .venv && source .venv/bin/activate
pip install pandas pyarrow duckdb numpy
```

품질 파이프라인 (원본 `orders.csv`는 저장소에 포함)

```bash
python3 clean_orders.py     # 1015 행 -> 1000 행 정제 완료 (검증 통과)
python3 quality_report.py   # quality_report.csv 생성
python3 check_rerun.py      # 재실행 결과 동일 여부
python3 crosscheck.py       # DuckDB로 교차 검증
```

성능 실측·분석 (대용량 데이터는 저장소에서 제외 — 스크립트로 다시 만듦)

```bash
python3 make_events.py      # events.csv 100만 행 (약 40 MB)
python3 speed.py            # Parquet 변환 + 속도·압축·파티션 측정
python3 transform.py && python3 timeseries.py   # orders_step1 / orders_enriched.parquet 생성
python3 sql_analysis.py     # 이후 roundtrip.py · funnel.py 등
```

## 7. 검증한 것

- 재실행: 같은 원본으로 두 번 정제 → `equals()` True, Parquet로 저장 후 다시 읽어도 True
- 교차 검증: Pandas 정제 결과를 DuckDB로 다시 측정 → 1,000행 · 결측 0 · 중복 0 · 카테고리 4
- 유효성: 음수 가격·수량, 미래 날짜, 미지 카테고리 모두 0건
- 지역별 매출: SQL 결과와 Pandas 결과의 차이 0
- 시드 고정: `make_orders.py`를 다시 돌려도 저장소의 `orders.csv`와 같은 파일이 나옴

## 8. 남은 개선점

- 3-1~3-4 분석용 `orders_step1.parquet`는 중복 제거 전(1,015행) 데이터 → 분석 입력을 `orders_clean.parquet`로 바꿔야 매출이 부풀지 않음
- 보정한 결측 30건을 구분할 표시 열이 없음 → `price_imputed` 플래그 추가 예정
- `validate_test.py`의 미래 날짜 검사는 실행일(`Timestamp.today()`) 기준이라 날짜에 따라 결과가 바뀔 수 있음
- 수업 단계별 코드를 이어 붙인 실습 파일이라 한 파일에 출력이 많음 → 파이프라인용(clean_orders)과 실습용 파일을 구분해 둠

## 9. 미니 과제 (3-5)

- 폴더: [mini/](mini/) — 대표 산출물과 섞이지 않도록 분리
- 값 범위 점검 추가 · 결측 처리 방식 비교(중앙값 보정 vs 행 버리기, 매출 합계 2.73% 차이) · events 100만 행 품질 측정을 DuckDB SQL로 (Pandas 대비 약 2배 빠르고 메모리 89 MB → 176 bytes)
