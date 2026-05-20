# 豆瓣电影影评爬虫 / Douban Movie Scraper

批量爬取豆瓣电影详情和用户评论，存入 MySQL 数据库，并导出为格式化的 Excel 文件。
Batch-crawl movie details and user comments from Douban, store them into MySQL database, and export to formatted Excel files.

## 运行 / Usage

### 1. 安装依赖 / Install Dependencies

```bash
pip install -r requirements.txt
```

确保电脑上已安装 Chrome 或 Edge 浏览器.

Make sure Chrome or Edge browser is installed on your machine.

### 2. 配置数据库 / Configure Database

确保 MySQL 服务已启动，并在 `douban_crawler.py` 和 `export_to_excel.py` 中确认以下配置正确。
Ensure the MySQL service is running, and confirm the following configuration in `douban_crawler.py` and `export_to_excel.py`:

```python
host='localhost'
user='root'
password='password'   # 修改为你的密码 / change to your password
database='movies'
```

### 3. 准备电影列表 / Prepare Movie List

编辑项目根目录下的 `douban_movie_list.csv`, 必须包含 `douban_id` 与 `movie_name` 两列. 豆瓣 ID 即电影页面 URL 中的数字部分, 例如 `https://movie.douban.com/subject/1292052/`.

Edit `douban_movie_list.csv` in the project root directory. It must contain two columns: `douban_id` and `movie_name`. The Douban ID is the numeric part in the movie page URL, e.g. `https://movie.douban.com/subject/1292052/`.

### 4. 运行爬虫 / Run the Crawler

```bash
python run.py
```

首次运行会弹出 Chrome 浏览器窗口, 需扫描二维码完成豆瓣登录. 登录后每部电影最多爬取 400 条评论.

A Chrome browser window will pop up. Scan the QR code to log in to Douban. After login, up to 400 comments will be crawled per movie.

### 5. 导出评论为 `.xlsx` / Export Comments to `.xlsx`

```bash
python export_to_excel.py
```

运行后生成 `douban_comments_export.xlsx`, 每部电影一个 Sheet. 

After running, `douban_comments_export.xlsx` will be generated, with one Sheet per movie.
