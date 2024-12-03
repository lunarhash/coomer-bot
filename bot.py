import os
import discord
from discord.ext import commands, tasks
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from scraper import CoomerScraper
from dropbox_sync import DropboxSync
import time
import aiohttp

# 加载环境变量
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))
DROPBOX_TOKEN = os.getenv('DROPBOX_TOKEN')
DROPBOX_REFRESH_TOKEN = os.getenv('DROPBOX_REFRESH_TOKEN')
DROPBOX_APP_KEY = os.getenv('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = os.getenv('DROPBOX_APP_SECRET')

# Bot 配置
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 存储进度消息的ID
progress_message = None
scraper_instance = None
current_task = None
dropbox_sync = None if not DROPBOX_TOKEN else DropboxSync(
    access_token=DROPBOX_TOKEN,
    refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

class ScraperConfig:
    def __init__(self):
        self.interval_minutes = 60
        self.urls = {
            'popular': 'https://coomer.su/posts/popular'
        }
        self.auto_sync = True  # 是否自动同步到 Dropbox
        self.load_config()
    
    def load_config(self):
        try:
            with open('config.json', 'r') as f:
                data = json.load(f)
                self.interval_minutes = data.get('interval_minutes', 60)
                self.urls = data.get('urls', self.urls)
                self.auto_sync = data.get('auto_sync', True)
        except FileNotFoundError:
            self.save_config()
    
    def save_config(self):
        with open('config.json', 'w') as f:
            json.dump({
                'interval_minutes': self.interval_minutes,
                'urls': self.urls,
                'auto_sync': self.auto_sync
            }, f, indent=2)

config = ScraperConfig()

async def update_progress(message, content):
    """更新进度消息"""
    if message:
        try:
            await message.edit(content=content)
        except discord.NotFound:
            channel = bot.get_channel(CHANNEL_ID)
            return await channel.send(content)
    else:
        channel = bot.get_channel(CHANNEL_ID)
        return await channel.send(content)

class DiscordScraperCallback:
    def __init__(self, message):
        self.message = message
        self.start_time = datetime.now()
        self.total_posts = 0
        self.processed_posts = 0
        self.total_videos = 0
        self.downloaded_videos = 0
        self.synced_videos = 0
        self.current_file = ""
        self.download_progress = 0
        self.sync_status = ""

    def format_time(self, seconds):
        if seconds < 60:
            return f"{seconds:.1f}秒"
        minutes = seconds / 60
        return f"{minutes:.1f}分钟"

    def get_progress_bar(self, percentage, length=20):
        filled = int(length * percentage / 100)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {percentage:.1f}%"

    async def update_progress(self):
        elapsed_time = (datetime.now() - self.start_time).total_seconds()
        
        # 构建进度消息
        message_lines = [
            "```",
            "🔄 爬取进度",
            "──────────────────────────",
            f"总帖子数：{self.total_posts}",
            f"已处理：{self.processed_posts}/{self.total_posts} {self.get_progress_bar(self.processed_posts/self.total_posts*100 if self.total_posts else 0)}",
            f"发现视频：{self.total_videos}",
            f"已下载：{self.downloaded_videos}",
            "──────────────────────────"
        ]

        # 如果正在下载，显示当前文件和进度
        if self.current_file and self.download_progress > 0:
            message_lines.extend([
                "📥 当前下载",
                f"文件：{self.current_file}",
                f"进度：{self.get_progress_bar(self.download_progress)}",
                "──────────────────────────"
            ])

        # 如果正在同步，显示同步状态
        if self.sync_status:
            message_lines.extend([
                "☁️ Dropbox同步",
                f"状态：{self.sync_status}",
                "──────────────────────────"
            ])

        message_lines.extend([
            f"⏱️ 运行时间：{self.format_time(elapsed_time)}",
            "```"
        ])

        await update_progress(self.message, "\n".join(message_lines))

    async def on_scraping_start(self, total_posts):
        self.total_posts = total_posts
        await self.update_progress()

    async def on_post_processed(self, post_num, skipped=False):
        self.processed_posts = post_num
        await self.update_progress()

    async def on_video_found(self, count):
        self.total_videos += count
        await self.update_progress()

    async def on_video_download_progress(self, filename, progress):
        self.current_file = filename
        self.download_progress = progress
        await self.update_progress()

    async def on_video_downloaded(self, filename):
        self.downloaded_videos += 1
        self.current_file = ""
        self.download_progress = 0
        await self.update_progress()

    async def on_video_synced(self, filename, success, message):
        self.sync_status = f"{'✅' if success else '❌'} {message}"
        if success:
            self.synced_videos += 1
        await self.update_progress()

@bot.event
async def on_ready():
    """Bot启动时的处理"""
    print(f'{bot.user} 已连接到Discord!')
    global current_task, scraping_task
    current_task = None  # 重置任务状态
    
    # 根据配置的间隔设置定时任务
    scraping_task.change_interval(minutes=config.interval_minutes)
    if not scraping_task.is_running():
        scraping_task.start()

@tasks.loop(minutes=1)
async def scraping_task():
    """定时任务"""
    global current_task
    
    if not current_task or current_task.done():
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            message = await channel.send("准备开始新的爬取任务...")
            current_task = asyncio.create_task(run_scraper(message))

async def run_scraper(message):
    """运行爬虫"""
    global scraper_instance, current_task, progress_message
    
    try:
        # 暂停定时任务
        scraping_task.cancel()
        
        progress_message = await message.channel.send("🔄 初始化爬虫...")
        callback = DiscordScraperCallback(progress_message)
        
        # 创建新的爬虫实例
        if not scraper_instance:
            scraper_instance = CoomerScraper()
        
        try:
            for url_name, url in config.urls.items():
                posts = await scraper_instance.run_async(url, callback)
                if posts:
                    # 下载视频并自动同步到 Dropbox
                    await scraper_instance.download_all_videos(posts, callback, dropbox_sync)
        except Exception as e:
            await message.channel.send(f"❌ 爬虫运行出错: {str(e)}")
        finally:
            scraper_instance.cleanup()
    finally:
        current_task = None  # 任务完成后重置状态
        # 重新启动定时任务
        if not scraping_task.is_running():
            scraping_task.start()

async def sync_videos(directory):
    """同步视频到 Dropbox"""
    if not dropbox_sync:
        return await bot.get_channel(CHANNEL_ID).send("❌ Dropbox 未配置")
    
    channel = bot.get_channel(CHANNEL_ID)
    message = await channel.send("🔄 开始同步视频到 Dropbox...")
    
    async def sync_callback(filename, success, status):
        await update_progress(message, 
            f"{'✅' if success else '❌'} {os.path.basename(filename)}: {status}")
    
    success, failed = await dropbox_sync.sync_directory(directory, sync_callback)
    
    await update_progress(message, 
        f"📤 同步完成!\n"
        f"成功: {success} 个文件\n"
        f"失败: {failed} 个文件")

@bot.command(name='sync')
async def sync_command(ctx):
    """手动同步视频到 Dropbox"""
    if not dropbox_sync:
        await ctx.send("❌ Dropbox 未配置")
        return
    
    for url_name in config.urls.keys():
        directory = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            'downloads',
            url_name
        )
        if os.path.exists(directory):
            await sync_videos(directory)

@bot.command(name='autosync')
async def autosync_command(ctx, enable: bool):
    """设置是否自动同步到 Dropbox"""
    config.auto_sync = enable
    config.save_config()
    await ctx.send(f"{'✅' if enable else '❌'} 自动同步已{'开启' if enable else '关闭'}")

@bot.command(name='storage')
async def storage_command(ctx):
    """显示 Dropbox 存储使用情况"""
    if not dropbox_sync:
        await ctx.send("❌ Dropbox 未配置")
        return
    
    used, total = dropbox_sync.get_storage_usage()
    if used is None or total is None:
        await ctx.send("❌ 获取存储信息失败")
        return
    
    used_gb = used / (1024**3)
    total_gb = total / (1024**3)
    percentage = (used / total) * 100
    
    await ctx.send(
        f"📊 Dropbox 存储使用情况:\n"
        f"已用: {used_gb:.2f} GB\n"
        f"总共: {total_gb:.2f} GB\n"
        f"使用率: {percentage:.1f}%"
    )

@bot.command(name='setinterval')
async def set_interval(ctx, minutes: int):
    """设置爬取间隔（分钟）"""
    if minutes < 1:
        await ctx.send("❌ 间隔时间必须大于1分钟")
        return
    
    config.interval_minutes = minutes
    config.save_config()
    
    # 取消当前任务
    scraping_task.cancel()
    # 使用新的间隔重新启动任务
    scraping_task.change_interval(minutes=minutes)
    scraping_task.start()
    
    await ctx.send(f"✅ 已设置爬取间隔为 {minutes} 分钟")

@bot.command(name='addurl')
async def add_url(ctx, name: str, url: str):
    """添加新的爬取URL"""
    if not url.startswith('https://coomer.su/'):
        await ctx.send("❌ 只支持 coomer.su 域名")
        return
    
    config.urls[name] = url
    config.save_config()
    await ctx.send(f"✅ 已添加新的爬取URL:\n名称: {name}\nURL: {url}")

@bot.command(name='removeurl')
async def remove_url(ctx, name: str):
    """移除爬取URL"""
    if name not in config.urls:
        await ctx.send("❌ 未找到指定的URL")
        return
    
    del config.urls[name]
    config.save_config()
    await ctx.send(f"✅ 已移除爬取URL: {name}")

@bot.command(name='listurls')
async def list_urls(ctx):
    """列出所有爬取URL"""
    if not config.urls:
        await ctx.send("没有配置的URL")
        return
    
    message = "📋 配置的URL列表:\n"
    for name, url in config.urls.items():
        message += f"- {name}: {url}\n"
    await ctx.send(message)

@bot.command(name='status')
async def status(ctx):
    """显示当前状态"""
    message = (
        f"⚙️ 当前配置:\n"
        f"爬取间隔: {config.interval_minutes} 分钟\n"
        f"URL数量: {len(config.urls)}\n"
        f"下次爬取: {scraping_task.next_iteration.strftime('%Y-%m-%d %H:%M:%S') if scraping_task.next_iteration else '未调度'}"
    )
    await ctx.send(message)

if __name__ == '__main__':
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            bot.run(TOKEN)
            break
        except (TimeoutError, ConnectionError, aiohttp.client_exceptions.ClientError) as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"连接错误: {e}")
                print(f"正在尝试重新连接... (尝试 {retry_count}/{max_retries})")
                time.sleep(5)  # 等待5秒后重试
            else:
                print("无法连接到 Discord，请检查网络连接或稍后再试")
                break
        except Exception as e:
            print(f"发生未知错误: {e}")
            break
