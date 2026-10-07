# check_robots.py
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url('https://quotes.toscrape.com/robots.txt')
rp.read()

print('수집 가능 여부:', rp.can_fetch('*', 'https://quotes.toscrape.com/'))
print('권고 간격:', rp.crawl_delay('*'))
