from __future__ import annotations

import os
import time
from datetime import datetime

import pymysql
import requests
from bs4 import BeautifulSoup

BASE = 'https://quotes.toscrape.com'
HEADERS = {'User-Agent': 'data-eng-class-crawler/1.0 (learning purpose)'}
DELAY_SEC = 1.0  # 크롤링 예절: 요청 간격 1초
FAILED_LOG = 'failed.log'

# (1) 접속 정보를 함수 밖 상수로 분리
#     비밀번호는 환경변수가 있으면 그것을 쓰고, 없으면 실습용 기본값을 사용
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '127.0.0.1'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'dataeng123'),
    'database': os.getenv('DB_NAME', 'shop'),
    'charset': 'utf8mb4',
}


# (2) 실패한 URL을 failed.log에 한 줄씩 추가 기록
def log_failure(url: str, error: Exception | None) -> None:
    reason = repr(error) if error else '429 응답이 재시도 횟수만큼 반복됨'
    with open(FAILED_LOG, 'a', encoding='utf-8') as f:
        f.write(f'{datetime.now():%Y-%m-%d %H:%M:%S}\t{url}\t{reason}\n')


def fetch(url: str, retries: int = 3) -> str:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
            if res.status_code == 429:
                print(f'  429 too many requests — {attempt}회차, 5초 대기')
                time.sleep(5)
                continue
            res.raise_for_status()
            return res.text
        except requests.RequestException as e:
            last_error = e
            print(f'  요청 실패({attempt}/{retries}): {e}')
            time.sleep(2 * attempt)      # 갈수록 더 오래 쉰다
    log_failure(url, last_error)         # 최종 실패 시에만 기록
    raise RuntimeError(f'{url} 수집 실패') from last_error


def parse(html: str) -> tuple[list[dict], str | None]:
    soup = BeautifulSoup(html, 'html.parser')
    rows = []
    for q in soup.select('div.quote'):
        rows.append({
            'author': q.select_one('small.author').get_text(strip=True),
            'quote_text': q.select_one('span.text').get_text(strip=True),
            'tags': ','.join(t.get_text(strip=True) for t in q.select('a.tag')),
        })
    next_link = soup.select_one('li.next a')
    next_url = BASE + next_link['href'] if next_link else None
    return rows, next_url


# 연결을 직접 열지 않고, 바깥에서 받은 conn을 사용
def load(conn: pymysql.connections.Connection, rows: list[dict]) -> int:
    saved = 0
    with conn.cursor() as cur:
        for r in rows:
            # INSERT IGNORE: UNIQUE 충돌(이미 수집한 명언)은 건너뜀
            saved += cur.execute(
                'INSERT IGNORE INTO quotes (author, quote_text, tags, crawled_at) '
                'VALUES (%s, %s, %s, %s)',
                (r['author'], r['quote_text'], r['tags'], datetime.now()),
            )
    conn.commit()  # 페이지 단위 커밋: 중간에 죽어도 앞 페이지는 보존
    return saved


def run(max_pages: int = 10) -> None:
    url = BASE + '/'
    conn = pymysql.connect(**DB_CONFIG)  # 연결은 실행 전체에서 한 번만
    try:
        for page in range(1, max_pages + 1):
            try:
                html = fetch(url)
            except RuntimeError as e:
                # 다음 페이지 주소는 이 페이지 HTML 안에 있으므로 더 진행할 수 없음
                print(f'page {page}: {e} → {FAILED_LOG} 기록 후 중단')
                break
            rows, next_url = parse(html)
            conn.ping(reconnect=True)    # 오래 쉬는 동안 끊겼으면 재연결
            saved = load(conn, rows)
            print(f'page {page}: parsed {len(rows)}, saved {saved}')
            if not next_url:
                break
            url = next_url
            time.sleep(DELAY_SEC)
    finally:
        conn.close()


if __name__ == '__main__':
    run()
