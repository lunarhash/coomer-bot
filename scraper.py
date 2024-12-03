import time
import os
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
import json
from datetime import datetime
import requests
from urllib.parse import urljoin
import asyncio

class CoomerScraper:
    def __init__(self):
        self.base_url = "https://coomer.su"
        self.popular_url = urljoin(self.base_url, "/posts/popular")
        self.setup_driver()
        self.download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'downloads')
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        # 初始化已爬取帖子的记录文件
        self.history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scraped_posts.json')
        self.scraped_posts = self.load_scraped_posts()

    def load_scraped_posts(self):
        """加载已爬取的帖子记录"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"加载历史记录时出错: {e}")
            return {}

    def save_scraped_posts(self):
        """保存已爬取的帖子记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.scraped_posts, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存历史记录时出错: {e}")

    def is_post_scraped(self, post_id, post_data):
        """检查帖子是否已经爬取过"""
        if post_id in self.scraped_posts:
            # 检查是否所有视频都已下载
            old_videos = set(v['filename'] for v in self.scraped_posts[post_id].get('videos', []))
            new_videos = set(v['filename'] for v in post_data.get('videos', []))
            if old_videos == new_videos:
                return True
        return False

    def add_to_scraped_posts(self, post_id, post_data):
        """添加帖子到已爬取记录"""
        self.scraped_posts[post_id] = post_data
        self.save_scraped_posts()

    def setup_driver(self):
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920x1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def random_sleep(self, min_seconds=2, max_seconds=5):
        time.sleep(random.uniform(min_seconds, max_seconds))

    def get_page_content(self, url, retries=3):
        for attempt in range(retries):
            try:
                print(f"Fetching content from {url}... (Attempt {attempt + 1}/{retries})")
                self.driver.get(url)
                
                # 等待页面加载完成
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # 随机延迟
                self.random_sleep()
                
                print("Page loaded successfully")
                return self.driver.page_source
            except (TimeoutException, WebDriverException) as e:
                print(f"Error on attempt {attempt + 1}: {e}")
                if attempt < retries - 1:
                    self.random_sleep(5, 10)
                    continue
                else:
                    print(f"Failed to fetch page after {retries} attempts")
                    return None
            except Exception as e:
                print(f"Unexpected error: {e}")
                return None

    async def run_async(self, url, callback=None):
        """异步运行爬虫"""
        print("开始爬取过程...")
        html_content = self.get_page_content(url)
        if html_content:
            soup = BeautifulSoup(html_content, 'html.parser')
            posts = soup.find_all('article', class_=['post-card', 'post-card--preview'])
            
            if callback:
                await callback.on_scraping_start(len(posts))
            
            parsed_posts = []
            skipped_posts = 0
            
            for i, post in enumerate(posts, 1):
                post_data = await self.process_post(post, i, len(posts), callback)
                if post_data:
                    parsed_posts.append(post_data)
            
            self.save_results(parsed_posts)
            return parsed_posts
        return []

    async def process_post(self, post, current_num, total_posts, callback=None):
        """处理单个帖子"""
        print(f"\n处理帖子 {current_num}/{total_posts}")
        post_data = {
            'post_id': post.get('data-id'),
            'service': post.get('data-service'),
            'user_id': post.get('data-user'),
            'url': post.find('a', class_='fancy-link')['href'] if post.find('a', class_='fancy-link') else None,
            'timestamp': None,
            'favorites': None,
            'attachments': None,
            'videos': []
        }

        # 检查是否已爬取过
        if post_data['post_id'] and self.is_post_scraped(post_data['post_id'], post_data):
            print(f"帖子 {post_data['post_id']} 已爬取过，跳过")
            if callback:
                await callback.on_post_processed(current_num, skipped=True)
            return None

        # 获取时间戳
        timestamp_elem = post.find('time', class_='timestamp')
        if timestamp_elem:
            post_data['timestamp'] = timestamp_elem['datetime']

        # 获取附件信息和收藏数
        footer_div = post.find('footer').find('div').find('div')
        if footer_div:
            text = footer_div.get_text(separator='\n').strip()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            for line in lines:
                if 'attachments' in line.lower():
                    post_data['attachments'] = line.split(' ')[0]
                elif 'favorites' in line.lower():
                    post_data['favorites'] = line.split(' ')[0]

        # 获取视频链接
        if post_data['url']:
            video_links = self.get_video_links(post_data['url'])
            post_data['videos'] = video_links
            
            if callback and video_links:
                await callback.on_video_found(len(video_links))

        # 添加到已爬取记录
        if post_data['post_id']:
            self.add_to_scraped_posts(post_data['post_id'], post_data)

        if callback:
            await callback.on_post_processed(current_num)

        return post_data

    def get_video_links(self, post_url):
        try:
            full_url = urljoin(self.base_url, post_url)
            html_content = self.get_page_content(full_url)
            if not html_content:
                return []

            soup = BeautifulSoup(html_content, 'html.parser')
            video_links = []
            
            # 查找所有视频下载链接
            for link in soup.find_all('a', class_='post__attachment-link'):
                href = link.get('href')
                if href and any(ext in href.lower() for ext in ['.mp4', '.mov', '.avi', '.wmv', '.flv']):
                    filename = link.get('download') or os.path.basename(href)
                    video_links.append({
                        'url': href,
                        'filename': filename
                    })
            
            print(f"Found {len(video_links)} video links")
            return video_links
        except Exception as e:
            print(f"Error getting video links: {e}")
            return []

    async def download_video(self, url, filename, callback=None, dropbox_sync=None):
        """下载视频文件"""
        try:
            print(f"正在下载视频: {filename}")
            
            # 随机延迟
            self.random_sleep()
            
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            file_path = os.path.join(self.download_dir, filename)
            file_size = int(response.headers.get('content-length', 0))
            
            with open(file_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = (downloaded / file_size) * 100 if file_size > 0 else 0
                        if callback:
                            await callback.on_video_download_progress(filename, progress)
            
            print(f"视频已保存到 {file_path}")
            
            # 下载完成后通知回调
            if callback:
                await callback.on_video_downloaded(filename)
            
            # 如果提供了 dropbox_sync，自动上传并删除本地文件
            if dropbox_sync and dropbox_sync.auto_sync:
                print(f"正在同步到 Dropbox: {filename}")
                success = await dropbox_sync.upload_file(file_path, callback)
                if success:
                    print(f"删除本地文件: {filename}")
                    os.remove(file_path)
            
            return True
        except Exception as e:
            print(f"下载视频时出错: {e}")
            return False

    async def download_all_videos(self, posts, callback=None, dropbox_sync=None):
        """下载所有视频"""
        total_videos = sum(len(post['videos']) for post in posts)
        if total_videos == 0:
            print("没有找到任何视频链接")
            return

        print(f"\n找到 {total_videos} 个视频链接。")
        print("视频将被下载到:", self.download_dir)
        
        if callback:
            await callback.on_video_found(total_videos)

        # 开始下载
        downloaded = 0
        for post in posts:
            for video in post['videos']:
                print(f"\n[{downloaded + 1}/{total_videos}] 正在下载: {video['filename']}")
                if await self.download_video(video['url'], video['filename'], callback, dropbox_sync):
                    downloaded += 1
                self.random_sleep(3, 7)  # 随机延迟，避免请求过快

        print(f"\n下载完成! 成功下载 {downloaded}/{total_videos} 个视频")

    def save_results(self, posts, filename='posts.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {filename}")

    async def run(self):
        print("开始爬取过程...")
        html_content = self.get_page_content(self.popular_url)
        if html_content:
            posts = await self.run_async(self.popular_url)
            print(f"\n找到 {len(posts)} 个帖子")
            
            # 询问用户是否下载视频
            await self.download_all_videos(posts)
            
            return posts
        return []

    def cleanup(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    scraper = CoomerScraper()
    try:
        results = asyncio.run(scraper.run())
    finally:
        scraper.cleanup()
