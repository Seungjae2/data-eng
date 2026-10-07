# crawler_pipeline.py — 수집(fetch) → 정제(parse) → 적재(load)
from __future__ import annotations

import time
from datetime import datetime

import pymysql
import requests
from bs4 import BeautifulSoup

BASE = 'https://quotes.toscrape.com'
HEADERS = {'User-Agent': 'data-eng-class-crawler/1.0 (learning purpose)'}
DELAY_SEC = 1.0  # 크롤링 예절: 요청 간격 1초


# crawler_pipeline.py 의 def fetch … return res.text 를 이것으로 바꿉니다
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


def load(rows: list[dict]) -> int:
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root',
                           password='dataeng123', database='shop', charset='utf8mb4')
    saved = 0
    try:
        with conn.cursor() as cur:
            for r in rows:
                # INSERT IGNORE: UNIQUE 충돌(이미 수집한 명언)은 건너뜀
                saved += cur.execute(
                    'INSERT IGNORE INTO quotes (author, quote_text, tags, crawled_at) '
                    'VALUES (%s, %s, %s, %s)',
                    (r['author'], r['quote_text'], r['tags'], datetime.now()),
                )
        conn.commit()
    finally:
        conn.close()
    return saved


def run(max_pages: int = 10) -> None:
    url = BASE + '/'
    for page in range(1, max_pages + 1):
        html = fetch(url)
        rows, next_url = parse(html)
        saved = load(rows)
        print(f'page {page}: parsed {len(rows)}, saved {saved}')
        if not next_url:
            break
        url = next_url
        time.sleep(DELAY_SEC)


if __name__ == '__main__':
    run()
