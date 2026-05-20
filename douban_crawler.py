import os
import time
import pickle
import pandas as pd
from bs4 import BeautifulSoup
import pymysql
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

EXCEL_PATH = "douban_movie_list.csv"
COOKIES_PATH = "douban_cookies.pkl"

_driver = None

def _ensure_logged_in(driver):
    driver.get('https://www.douban.com/')
    time.sleep(2)

    if os.path.exists(COOKIES_PATH):
        try:
            cookies = pickle.load(open(COOKIES_PATH, 'rb'))
            for cookie in cookies:
                cookie = {k: v for k, v in cookie.items() if k in {'name', 'value', 'domain', 'path', 'secure', 'expiry'}}
                driver.add_cookie(cookie)
            driver.get('https://www.douban.com/')
            time.sleep(2)
            if _is_logged_in(driver):
                print('Logged in automatically via saved cookies')
                return
            else:
                print('Cookies have expired, please log in again')
        except Exception as e:
            print(e)

    print('Please scan the QR code to log in to Douban in the pop-up browser window')
    input('After successful login, press Enter to continue the crawler')
    driver.get('https://www.douban.com/')
    time.sleep(2)
    if not _is_logged_in(driver):
        print('Verification failed, cookies will not be saved')
    else:
        try:
            pickle.dump(driver.get_cookies(), open(COOKIES_PATH, 'wb'))
            print('Login successful, cookies have been saved')
        except Exception as e:
            print(e)

def _is_logged_in(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return bool(soup.find('a', {'class': 'lnk-user'}) or soup.find('span', {'class': 'usr-name'}))

def _get_driver():
    global _driver
    if _driver is None:
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        _driver = webdriver.Chrome(options=chrome_options)
        _driver.implicitly_wait(5)
        _ensure_logged_in(_driver)
    return _driver

def _close_driver():
    global _driver
    if _driver:
        _driver.quit()
        _driver = None

def fromurl2soup(url, wait_for_comments=False):
    driver = _get_driver()
    driver.get(url)
    if wait_for_comments:
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'comments'))
            )
        except:
            pass
    time.sleep(1)
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup

def load_movie_ids():
    df = pd.read_csv(EXCEL_PATH, encoding='gbk')
    movie_ids = df['douban_id'].tolist()
    print(f"A total of  {len(movie_ids)} movies have been read.")
    return movie_ids

def parse_movie_detail(douban_id, title_cn, release_date_cn):
    def find_pure_text_tag(find_key, save_name, tag, join=False):
        for i in range(len(tag)):
            if tag[i] == find_key:
                start = i
                end = start
                for j in range(i, len(tag)):
                    if tag[j] == '\n':
                        end = j
                        break
                if end - start == 2:
                    movieinfo[save_name] = tag[i + 1].strip()
                elif end - start > 2:
                    movieinfo[save_name] = tag[i + 1:j]
                break
        try:
            movieinfo[save_name]
            if join:
                movieinfo[save_name] = ''.join(movieinfo[save_name]).strip()
        except:
            movieinfo[save_name] = None

    movieinfo = {}
    url = f"https://movie.douban.com/subject/{douban_id}/"
    soup_movie = fromurl2soup(url)

    movieinfo['douban_id'] = str(douban_id)
    movieinfo['title_cn'] = title_cn
    movieinfo['release_date_cn'] = str(release_date_cn)

    pointer = soup_movie.find('div', {'id': 'content'})

    try:
        movieinfo['title'] = pointer.find('span', {'property': 'v:itemreviewed'}).get_text(strip=True)
    except:
        movieinfo['title'] = None

    try:
        year_tag = pointer.find('span', {'class': 'year'})
        if year_tag:
            movieinfo['year'] = year_tag.get_text(strip=True)[1:-1]
        else:
            movieinfo['year'] = None
    except:
        movieinfo['year'] = None

    pointer = pointer.find('div', {'class': 'article'})

    try:
        directorlist = pointer.find('span', string='导演') \
            .find_parent('span') \
            .find('span', {'class': 'attrs'}) \
            .find_all('a')
        directorlist = [d.get_text(strip=True) for d in directorlist]
    except:
        directorlist = []
    movieinfo['director'] = directorlist

    try:
        scriptwriterlist = pointer.find('span', string='编剧') \
            .find_parent('span') \
            .find('span', {'class': 'attrs'}) \
            .find_all('a')
        scriptwriterlist = [s.get_text(strip=True) for s in scriptwriterlist]
    except:
        scriptwriterlist = []
    movieinfo['scriptwriter'] = scriptwriterlist

    try:
        lead_performer_spanlist = pointer.find('span', string='主演') \
            .find_parent('span') \
            .find('span', {'class': 'attrs'}) \
            .find_all('span')
        if lead_performer_spanlist == []:
            lead_performer_a_list = pointer.find('span', string='主演') \
                .find_parent('span') \
                .find('span', {'class': 'attrs'}) \
                .find_all('a')
            lead_performerlist = [a.get_text(strip=True) for a in lead_performer_a_list]
        else:
            lead_performerlist = [s.find('a').get_text(strip=True) for s in lead_performer_spanlist]
    except:
        lead_performerlist = []
    movieinfo['lead_performer'] = lead_performerlist

    genrelist = pointer.find_all('span', {'property': 'v:genre'})
    movieinfo['genre'] = [g.get_text(strip=True) for g in genrelist]

    try:
        info_div = pointer.find('span', string='制片国家/地区:').find_parent('div', {'id': 'info'})
        info_text_list = list(info_div.strings)
        find_pure_text_tag('制片国家/地区:', 'produced_country_or_region', info_text_list)
        find_pure_text_tag('语言:', 'language', info_text_list)
    except:
        movieinfo['produced_country_or_region'] = None
        movieinfo['language'] = None

    try:
        initial_release_date_span_list = pointer.find_all('span', {'property': 'v:initialReleaseDate'})
        movieinfo['initial_release_date'] = [r.get_text(strip=True) for r in initial_release_date_span_list]
    except:
        movieinfo['initial_release_date'] = []

    try:
        info_div = pointer.find('div', {'id': 'info'})
        info_text_list = list(info_div.strings)
        find_pure_text_tag('片长:', 'runtime', info_text_list, join=True)
        find_pure_text_tag('又名:', 'also_known_as', info_text_list)
        find_pure_text_tag('IMDb:', 'IMDb', info_text_list)
        find_pure_text_tag('官方网站:', 'official_site', info_text_list, join=True)
    except:
        movieinfo['runtime'] = None
        movieinfo['also_known_as'] = None
        movieinfo['IMDb'] = None
        movieinfo['official_site'] = None

    try:
        movieinfo['summary'] = soup_movie.find('span', {'class': 'all hidden'}).get_text(strip=True)
    except:
        try:
            movieinfo['summary'] = soup_movie.find('span', {'property': 'v:summary'}).get_text(strip=True)
        except:
            movieinfo['summary'] = None

    try:
        rating_wrap = soup_movie.find('div', {'class': 'rating_wrap clearbox'})
        movieinfo['rating'] = rating_wrap.find('strong', {'class': 'll rating_num'}).get_text(strip=True)
        movieinfo['nums_of_rating_people'] = rating_wrap.find('a', {'class': 'rating_people'}) \
            .find('span', {'property': 'v:votes'}).get_text(strip=True)

        ratings_on_weight = {}
        for i in range(1, 6):
            try:
                ratings_on_weight[f'{i} star'] = rating_wrap.find('span', {'class': f'stars{i} starstop'}) \
                    .find_next_sibling('span', {'class': 'rating_per'}).get_text(strip=True)
            except:
                ratings_on_weight[f'{i} star'] = None
        movieinfo['ratings_on_weight'] = ratings_on_weight

        try:
            rating_text_list = list(rating_wrap.find_parent('div', {'id': 'interest_sectl'})
                                    .find('div', {'class': 'rating_betterthan'}).strings)
            rating_text_list = [t.strip() for t in rating_text_list if t.strip()]
            movieinfo['rating_betterthan'] = [rating_text_list[i] + rating_text_list[i + 1]
                                               for i in range(0, len(rating_text_list), 2)]
        except:
            movieinfo['rating_betterthan'] = []
    except:
        movieinfo['rating'] = None
        movieinfo['nums_of_rating_people'] = None
        movieinfo['ratings_on_weight'] = {}
        movieinfo['rating_betterthan'] = []

    try:
        movieinfo['comments_site'] = soup_movie.find('div', {'id': 'comments-section'}) \
            .find('h2') \
            .find('a') \
            .get('href')
    except:
        movieinfo['comments_site'] = None

    return movieinfo

def parse_comments_site(comments_url, max_comments=500):
    comments_divs = []

    def parse_comments_site_page(comments_page_url):
        nonlocal comments_divs
        comment_page_soup = fromurl2soup(comments_page_url, wait_for_comments=True)
        pointer = comment_page_soup.find('div', {'class': 'mod-bd', 'id': 'comments'})
        items = pointer.find_all('div', {'class': 'comment-item'})
        comments_divs.extend(items)
        next_url = None
        try:
            paginator = pointer.find('div', {'id': 'paginator'})
            all_links = paginator.find_all('a')
            next_url = None
            for link in all_links:
                text = link.get_text(strip=True)
                if '后' in text or 'next' in text.lower():
                    next_url = urljoin(comments_page_url, link.get('href'))
                    break
            if next_url:
                pass
            elif len(comments_divs) == 0:
                print("no comment found in this page.")
            else:
                print("Next page link not found, already on the last page.")
        except Exception as e:
            print(e)
        return next_url

    pageurl = comments_url
    count = 0
    for _ in range(999):
        count += 1
        if pageurl is None:
            break
        pageurl = parse_comments_site_page(pageurl)
        print(f"Page {count}, current total {len(comments_divs)} comments")
        if len(comments_divs) >= max_comments:
            break

    return comments_divs[:max_comments]

def star(str_list):
    star_pattern = re.compile(r'allstar(\d+)')
    for s in str_list:
        match = re.match(star_pattern, s)
        if match:
            return int(match.group(1)) / 10
    return None

def parse_comments_div(comments_div, movie_id):
    comment = {}
    pointer = comments_div.find('div', {'class': 'comment'})
    comment['movie_id'] = movie_id
    comment['user'] = pointer.find('span', {'class': 'comment-info'}).find('a').get_text(strip=True)
    try:
        comment['star'] = star(pointer.find('span', {'class': 'comment-info'})
                                .find('span', class_=lambda x: x and 'allstar' in x)
                                .get('class'))
    except:
        comment['star'] = None
    comment['time'] = pointer.find('span', {'class': 'comment-time'}).get_text(strip=True)
    comment['useful'] = pointer.find('span', {'class': 'votes vote-count'}).get_text(strip=True)
    try:
        comment['content'] = pointer.find('p', {'class': 'comment-content'}).get_text(strip=True)
    except:
        comment['content'] = None
    return comment

def create_database():
    with pymysql.connect(host='localhost', user='root', password='password') as db:
        with db.cursor() as cursor:
            sql = "CREATE DATABASE IF NOT EXISTS movies"
            try:
                cursor.execute(sql)
                print('Database created successfully.')
            except pymysql.MySQLError as e:
                print(e)

def create_movies_table():
    with pymysql.connect(host='localhost', user='root', password='password', database='movies') as db:
        with db.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS comments_list")
            cursor.execute("DROP TABLE IF EXISTS movies_list")
            sql = """CREATE TABLE movies_list(
                id INT AUTO_INCREMENT PRIMARY KEY,
                douban_id VARCHAR(20) NOT NULL,
                title_cn VARCHAR(100),
                release_date_cn VARCHAR(20),
                title VARCHAR(200),
                year VARCHAR(20),
                director VARCHAR(1000),
                scriptwriter VARCHAR(1000),
                lead_performer VARCHAR(2000),
                genre VARCHAR(200),
                produced_country_or_region VARCHAR(200),
                language VARCHAR(100),
                initial_release_date VARCHAR(500),
                runtime VARCHAR(100),
                also_known_as VARCHAR(500),
                IMDb VARCHAR(30),
                official_site VARCHAR(200),
                summary VARCHAR(5000),
                rating VARCHAR(20),
                nums_of_rating_people VARCHAR(20),
                ratings_on_weight VARCHAR(200),
                rating_betterthan VARCHAR(500),
                comments_site VARCHAR(200))
                """
            try:
                cursor.execute(sql)
                print('Movie data table created successfully.')
            except pymysql.MySQLError as e:
                print(e)

def create_comments_table():
    with pymysql.connect(host='localhost', user='root', password='password', database='movies') as db:
        with db.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS comments_list")
            sql = """CREATE TABLE comments_list(
                id INT AUTO_INCREMENT PRIMARY KEY,
                movie_id INT,
                user VARCHAR(50) NOT NULL,
                star VARCHAR(20),
                time VARCHAR(50) NOT NULL,
                useful VARCHAR(40) NOT NULL,
                content VARCHAR(5000),
                CONSTRAINT fk_parent FOREIGN KEY (movie_id) REFERENCES movies_list(id))
                """
            try:
                cursor.execute(sql)
                print('Comment data table created successfully.')
            except pymysql.MySQLError as e:
                print(e)

def insert_movie_table(movieinfo):
    fields = ['douban_id', 'title_cn', 'release_date_cn', 'title', 'year', 'director',
              'scriptwriter', 'lead_performer', 'genre', 'produced_country_or_region',
              'language', 'initial_release_date', 'runtime', 'also_known_as', 'IMDb',
              'official_site', 'summary', 'rating', 'nums_of_rating_people',
              'ratings_on_weight', 'rating_betterthan', 'comments_site']
    values = []
    for f in fields:
        v = movieinfo.get(f, '')
        values.append(str(v) if v is not None else '')
    values = tuple(values)
    db = pymysql.connect(host='localhost', user='root', password='password', database='movies')
    try:
        with db.cursor() as cursor:
            sql = f"""INSERT INTO movies_list({','.join(fields)})
                values({','.join(['%s'] * len(fields))})"""
            cursor.execute(sql, values)
            db.commit()
            cursor.execute("SELECT LAST_INSERT_ID()")
            movie_id = cursor.fetchone()[0]
        db.close()
        print(f"Data for the movie '{movieinfo.get('title_cn', '')}' inserted successfully.")
        return movie_id
    except pymysql.MySQLError as e:
        db.rollback()
        db.close()
        print(e)
        return None

def insert_comments_table(comment):
    values = (comment['movie_id'], comment['user'], comment['star'],
              comment['time'], comment['useful'], comment['content'])
    with pymysql.connect(host='localhost', user='root', password='password', database='movies') as db:
        with db.cursor() as cursor:
            sql = """INSERT INTO comments_list(movie_id,user,star,time,useful,content)
                values(%s,%s,%s,%s,%s,%s)"""
            try:
                cursor.execute(sql, values)
                db.commit()
                print(f"Comment from '{comment['user']}' inserted successfully.")
            except pymysql.MySQLError as e:
                db.rollback()
                print(e)

create_database()
create_movies_table()
create_comments_table()

_get_driver()

try:
    df = pd.read_csv(EXCEL_PATH, encoding='gbk')

    for idx, row in df.iterrows():
        douban_id = row['douban_id']
        title_cn = row['movie_name']
        release_date_cn = ""

        print(f"\nCurrently crawling: {title_cn} (douban_id: {douban_id})")
        movieinfo = parse_movie_detail(douban_id, title_cn, release_date_cn)
        movie_id = insert_movie_table(movieinfo)

        if movieinfo.get('comments_site'):
            comments_divs = parse_comments_site(movieinfo['comments_site'], max_comments=500)
            for comments_div in comments_divs:
                comment = parse_comments_div(comments_div, movie_id)
                insert_comments_table(comment)

finally:
    _close_driver()
print("\nAll crawling completed.")
