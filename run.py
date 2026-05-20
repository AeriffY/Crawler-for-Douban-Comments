"""
豆瓣电影影评爬虫
根据 Excel 表格中的 douban_id 爬取电影详情和评论
"""
import os
import sys
import subprocess

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    crawler_path = os.path.join(current_dir, "douban_crawler.py")

    if not os.path.exists(crawler_path):
        print(f"错误：找不到爬虫文件 '{crawler_path}'")
        return 1

    print("开始执行豆瓣电影影评爬虫（按 douban_movie_list.csv 中的电影列表）...")
    try:
        # 执行爬虫脚本
        result = subprocess.run([sys.executable, crawler_path], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"爬虫执行失败: {e}")
        return e.returncode
    except Exception as e:
        print(f"发生错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())