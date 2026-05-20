# 豆瓣电影影评爬虫

根据豆瓣电影 ID 列表批量爬取电影详情和用户评论，并存储至 MySQL 数据库，支持导出为格式化的 Excel 文件。


## 运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```
此外, 确保你的电脑上已经安装了 Chrome 浏览器或 Edge 浏览器.

### 2. 配置数据库

确保 MySQL 服务已启动, 并在 `douban_crawler.py` 和 `export_to_excel.py` 中确认以下配置正确：

```python
host='localhost'
user='root'
password='password'   #修改为你的密码
database='movies'
```

### 3. 准备电影列表

编辑项目根目录下的 `douban_movie_list.csv`, 必须包含 `douban_id` 与 `movie_name` 两列. 

豆瓣 ID 即电影页面 URL 中的数字部分, 例如`https://movie.douban.com/subject/1292052/`

### 4. 运行爬虫

```bash
python run.py
```

会弹出 Chrome 浏览器窗口, 需扫描二维码完成豆瓣登录. 登录后至多爬取 400 条评论.

### 5. 导出评论为 `.xlsx`

```bash
python export_to_excel.py
```

运行后生成 `douban_comments_export.xlsx`，每部电影一个 Sheet.
