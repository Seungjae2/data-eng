# 2주차 산출물 — 쇼핑몰 ERD 설계 + 크롤링 파이프라인

## 1. ERD 설계서

- 파일: [ERD_설계서.md](ERD_설계서.md) (ERD · 엔터티 정의 · 관계 · 정규화 근거 · 반정규화 결정 · DDL)
- 표 4개: customers · products · orders · order_items
- N:M(주문↔상품)을 order_items 교차 표로 해소

## 2. 크롤러

- 대상: https://quotes.toscrape.com (robots.txt가 없어 404 → 파서가 "허용"으로 판단. 크롤링 연습용 공개 사이트)
- 구조: fetch(수집) → parse(정제) → load(적재) 3함수 분리
- 예절: User-Agent 표기 · 요청 간격 1초 · robots.txt 사전 확인
- 안전장치: 요청 실패 시 최대 3회 재시도(점점 길게 대기), 429 응답 시 5초 대기
- 중복 방지: quotes 표의 UNIQUE(author, quote_text) 제약 + INSERT IGNORE
- 수집 범위: 전체 10페이지 (`max_pages=10`)
- 본문 칸은 TEXT: 500자가 넘는 명언이 있어 VARCHAR(500)이면 INSERT IGNORE가 경고만 내고 잘라 넣음

## 3. 실행 방법

```bash
docker start de-mysql
python3 -m venv .venv && source .venv/bin/activate   # Windows(WSL2)·macOS·리눅스 모두 같습니다
pip install requests beautifulsoup4 pymysql
```

quotes 표가 없다면 먼저 만듭니다.

```bash
docker exec -it -e LANG=C.UTF-8 de-mysql mysql -uroot -pdataeng123 shop
```

```sql
CREATE TABLE quotes (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    author     VARCHAR(100) NOT NULL,
    quote_text TEXT NOT NULL,
    tags       VARCHAR(300),
    crawled_at DATETIME NOT NULL,
    UNIQUE KEY uq_author_text (author, quote_text(200))
);
```

```bash
python3 check_robots.py       # 수집 가능 여부 확인
python3 crawler_pipeline.py   # 10페이지 수집·적재
python3 crawler_pipeline2.py  # 개선판 (아래 5번 참고) — 둘 중 하나만 실행해도 됩니다
```

## 4. 검증한 것

- 첫 실행: 페이지마다 parsed 10 / saved 10, 전체 10페이지 = 100건
- 재실행: 페이지마다 parsed 10 / saved 0 (DB 제약이 중복을 막음)
- SELECT COUNT(*) FROM quotes → 100

## 5. 개선한 점과 남은 개선점

`crawler_pipeline2.py`에 반영한 것:

- DB 접속 정보를 `DB_CONFIG`로 분리하고 환경변수(`DB_HOST`, `DB_PASSWORD` 등)를 우선 사용 (없으면 실습용 기본값)
- 재시도 끝에 실패한 URL을 `failed.log`에 시각·URL·원인과 함께 기록하고, 다음 페이지 주소를 알 수 없으므로 거기서 중단
- DB 연결을 페이지마다 새로 열지 않고 실행 전체에서 한 번만 열어 재사용, `conn.ping(reconnect=True)`로 끊긴 연결 복구
- 페이지 단위 커밋으로 중간에 실패해도 앞 페이지까지는 보존

남은 개선점:

- tags를 쉼표 문자열로 저장 중 (1NF 위반) → quote_tags 교차 표로 분리 예정
