# Coomer.su 视频爬虫 & Discord 机器人

这是一个功能强大的爬虫工具，可以从 Coomer.su 下载视频，并通过 Discord 机器人进行控制。支持自动同步到 Dropbox，让您可以随时随地访问下载的内容。

## 主要功能

- 🤖 Discord 机器人控制
  - 设置爬取间隔
  - 添加/删除爬取链接
  - 查看当前状态
  - 实时进度显示

- 📥 视频下载
  - 自动检测视频链接
  - 显示下载进度条
  - 避免重复下载
  - 支持批量下载

- ☁️ Dropbox 集成
  - 自动同步到 Dropbox
  - 同步完成后自动清理本地文件
  - 查看存储使用情况
  - 支持手动/自动同步模式

## 安装说明

1. 克隆仓库：
```bash
git clone [你的仓库地址]
cd [项目目录]
```

2. 创建虚拟环境：
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
创建 `.env` 文件并添加以下配置：
```
# Discord 配置
DISCORD_TOKEN=你的Discord机器人Token
DISCORD_CHANNEL_ID=你的Discord频道ID

# Dropbox 配置
DROPBOX_TOKEN=你的Dropbox访问令牌
DROPBOX_REFRESH_TOKEN=你的Dropbox刷新令牌
DROPBOX_APP_KEY=你的Dropbox应用密钥
DROPBOX_APP_SECRET=你的Dropbox应用密钥
```

## Discord 机器人命令

- `!setinterval <分钟>` - 设置爬取间隔
- `!addurl <名称> <链接>` - 添加新的爬取链接
- `!removeurl <名称>` - 删除爬取链接
- `!listurls` - 显示所有爬取链接
- `!status` - 查看当前状态
- `!sync` - 手动同步到 Dropbox
- `!autosync <true/false>` - 开启/关闭自动同步
- `!storage` - 查看 Dropbox 存储使用情况

## 运行方式

```bash
python bot.py
```

## 最新更新

- ✨ 新增实时下载进度显示
- 🔄 优化 Dropbox 同步流程
- 📊 美化进度显示界面
- 🔧 修复任务状态管理问题
- ⚡️ 提升运行稳定性

## 注意事项

- 请确保您有足够的 Dropbox 存储空间
- 建议使用代理以提高访问稳定性
- 首次使用需要配置 Discord 和 Dropbox 的认证信息
- 下载的文件会自动按来源分类存储

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
