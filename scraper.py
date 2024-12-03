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

    def download_video(self, url, filename):
        try:
            print(f"Downloading video from {url}...")
            
            # 随机延迟
            self.random_sleep()
            
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            file_path = os.path.join(self.download_dir, filename)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"Video saved to {file_path}")
            return True
        except Exception as e:
            print(f"Error downloading video: {e}")
            return False

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

    def parse_posts(self, html_content):
        if not html_content:
            return []

        soup = BeautifulSoup(html_content, 'html.parser')
        posts = soup.find_all('article', class_=['post-card', 'post-card--preview'])
        
        parsed_posts = []
        for i, post in enumerate(posts, 1):
            print(f"\nProcessing post {i}/{len(posts)}")
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

            parsed_posts.append(post_data)
            # 每处理完一个帖子后保存一次结果
            self.save_results(parsed_posts)

        return parsed_posts

    def download_all_videos(self, posts):
        """下载所有帖子中的视频"""
        total_videos = sum(len(post['videos']) for post in posts)
        if total_videos == 0:
            print("没有找到任何视频链接")
            return

        print(f"\n找到 {total_videos} 个视频链接。")
        print("视频将被下载到:", self.download_dir)
        
        # 显示所有视频信息
        for i, post in enumerate(posts, 1):
            if post['videos']:
                print(f"\n帖子 {i}:")
                for video in post['videos']:
                    print(f"- {video['filename']}")

        # 询问用户是否下载
        response = input("\n是否下载这些视频？(y/n): ").lower().strip()
        if response != 'y':
            print("取消下载")
            return

        # 开始下载
        downloaded = 0
        for post in posts:
            for video in post['videos']:
                print(f"\n[{downloaded + 1}/{total_videos}] 正在下载: {video['filename']}")
                if self.download_video(video['url'], video['filename']):
                    downloaded += 1
                self.random_sleep(3, 7)  # 随机延迟，避免请求过快

        print(f"\n下载完成! 成功下载 {downloaded}/{total_videos} 个视频")

    def save_results(self, posts, filename='posts.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
            print(f"Results saved to {filename}")

    def run(self):
        print("开始爬取过程...")
        html_content = self.get_page_content(self.popular_url)
        if html_content:
            posts = self.parse_posts(html_content)
            self.save_results(posts)
            print(f"\n找到 {len(posts)} 个帖子")
            
            # 询问用户是否下载视频
            self.download_all_videos(posts)
            
            return posts
        return []

    def cleanup(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

if __name__ == "__main__":
    scraper = CoomerScraper()
    try:
        results = scraper.run()
    finally:
        scraper.cleanup()
