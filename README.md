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

## 详细安装教程

### 1. 基础环境准备

1. 安装 Python（3.7+）
   ```bash
   # 检查 Python 版本
   python --version
   # 如果版本低于 3.7，请从 python.org 下载安装新版本
   ```

2. 安装 Chrome 浏览器
   - 从 [Chrome 官网](https://www.google.com/chrome/) 下载安装
   - 确保 Chrome 版本与 ChromeDriver 版本匹配

3. 安装 Git（如果尚未安装）
   ```bash
   # Mac（使用 Homebrew）
   brew install git
   
   # Windows
   # 从 https://git-scm.com/download/win 下载安装
   ```

### 2. 项目设置

1. 克隆仓库：
   ```bash
   git clone [你的仓库地址]
   cd [项目目录]
   ```

2. 创建并激活虚拟环境：
   ```bash
   # 创建虚拟环境
   python -m venv .venv
   
   # MacOS/Linux 激活虚拟环境
   source .venv/bin/activate
   
   # Windows 激活虚拟环境
   .venv\Scripts\activate
   
   # 确认虚拟环境已激活（应该看到命令行前面有 (.venv)）
   ```

3. 安装依赖：
   ```bash
   # 升级 pip
   python -m pip install --upgrade pip
   
   # 安装项目依赖
   pip install -r requirements.txt
   ```

### 3. Discord 机器人配置

1. 创建 Discord 机器人：
   - 访问 [Discord Developer Portal](https://discord.com/developers/applications)
   - 点击 "New Application"，创建新应用
   - 进入 "Bot" 页面，点击 "Add Bot"
   - 开启 "Message Content Intent" 权限
   - 复制机器人 Token

2. 邀请机器人到服务器：
   - 在 "OAuth2 > URL Generator" 页面
   - 选择 "bot" 和 "applications.commands" 权限
   - 在 Bot Permissions 中选择必要权限（至少需要：Read Messages/View Channels、Send Messages、Embed Links）
   - 使用生成的链接邀请机器人到你的服务器

3. 获取频道 ID：
   - 在 Discord 设置中开启开发者模式
   - 右键点击目标频道，选择 "Copy ID"

### 4. Dropbox 配置

1. 创建 Dropbox 应用：
   - 访问 [Dropbox App Console](https://www.dropbox.com/developers/apps)
   - 点击 "Create app"
   - 选择 "Scoped access"
   - 选择 "Full Dropbox" 访问权限
   - 输入应用名称

2. 配置权限：
   - 在 "Permissions" 标签页中添加以下权限：
     - files.content.write
     - files.content.read
     - sharing.write

3. 获取密钥：
   - 在 "Settings" 标签页复制 App key 和 App secret
   - 在 "OAuth2" 标签页生成访问令牌
   - 获取并保存 Refresh token

### 5. 环境配置

1. 创建环境变量文件：
   ```bash
   # 在项目根目录创建 .env 文件
   touch .env   # MacOS/Linux
   # 或
   echo.> .env  # Windows
   ```

2. 编辑 .env 文件，添加以下内容：
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

### 6. 启动项目

1. 确保虚拟环境已激活：
   ```bash
   # 命令行前面应该显示 (.venv)
   # 如果没有，请执行激活命令
   source .venv/bin/activate  # MacOS/Linux
   # 或
   .venv\Scripts\activate    # Windows
   ```

2. 运行机器人：
   ```bash
   python bot.py
   ```

3. 验证运行状态：
   - 在 Discord 中输入 `!status` 检查机器人状态
   - 使用 `!help` 查看所有可用命令

### 7. 常见问题解决

1. Chrome 驱动问题：
   - 确保 Chrome 浏览器已安装
   - 如果出现 ChromeDriver 错误，请确认 Chrome 版本并安装匹配的 ChromeDriver

2. 权限问题：
   - 确保 Discord 机器人有足够的频道权限
   - 检查 Dropbox 应用权限是否配置正确

3. 网络问题：
   - 如果出现连接超时，检查网络连接
   - 考虑使用代理服务器

4. 存储空间：
   - 定期检查 Dropbox 存储空间使用情况
   - 使用 `!storage` 命令查看当前使用状态

### 8. 更新和维护

1. 更新代码：
   ```bash
   git pull origin main
   ```

2. 更新依赖：
   ```bash
   pip install -r requirements.txt --upgrade
   ```

3. 定期维护：
   - 检查 logs 文件夹大小
   - 清理临时文件
   - 更新 Discord 和 Dropbox 令牌（如需要）

## Ubuntu 服务器部署指南

### 1. 系统准备

1. 更新系统包：
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

2. 安装必要的系统依赖：
   ```bash
   sudo apt install -y python3-pip python3-venv git wget unzip curl
   ```

3. 安装 Chrome 和 ChromeDriver：
   ```bash
   # 安装 Chrome
   wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
   sudo dpkg -i google-chrome-stable_current_amd64.deb
   sudo apt --fix-broken install -y
   
   # 获取 Chrome 版本
   chrome_version=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1)
   
   # 下载对应版本的 ChromeDriver
   wget -N "https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$chrome_version.0.xxxx.0/linux64/chromedriver-linux64.zip"
   unzip chromedriver-linux64.zip
   sudo mv chromedriver-linux64/chromedriver /usr/local/bin/
   sudo chmod +x /usr/local/bin/chromedriver
   ```

### 2. 项目部署

1. 克隆项目：
   ```bash
   git clone [你的仓库地址]
   cd [项目目录]
   ```

2. 设置 Python 环境：
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. 配置环境变量：
   ```bash
   cp .env.example .env
   nano .env  # 编辑配置文件
   ```

### 3. 使用 Screen 后台运行

1. 安装 Screen：
   ```bash
   sudo apt install screen -y
   ```

2. 创建新的 Screen 会话：
   ```bash
   screen -S discord-bot
   ```

3. 在 Screen 会话中运行机器人：
   ```bash
   source .venv/bin/activate
   python3 bot.py
   ```

4. 分离 Screen 会话（保持程序运行）：
   - 按 `Ctrl + A`，然后按 `D`

5. 常用 Screen 命令：
   ```bash
   screen -ls                 # 查看所有会话
   screen -r discord-bot      # 重新连接到会话
   screen -X -S discord-bot quit  # 结束会话
   ```

### 4. 设置开机自启（可选）

1. 创建系统服务文件：
   ```bash
   sudo nano /etc/systemd/system/discord-bot.service
   ```

2. 添加以下内容：
   ```ini
   [Unit]
   Description=Discord Bot Service
   After=network.target
   
   [Service]
   Type=simple
   User=你的用户名
   WorkingDirectory=/完整路径/到你的项目目录
   Environment="PATH=/完整路径/到你的项目目录/.venv/bin"
   ExecStart=/完整路径/到你的项目目录/.venv/bin/python bot.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. 启用并启动服务：
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable discord-bot
   sudo systemctl start discord-bot
   ```

4. 查看服务状态：
   ```bash
   sudo systemctl status discord-bot
   ```

### 5. 日志管理

1. 查看实时日志：
   ```bash
   # 如果使用 Screen
   screen -r discord-bot
   
   # 如果使用 systemd
   sudo journalctl -u discord-bot -f
   ```

2. 设置日志轮转（可选）：
   ```bash
   sudo nano /etc/logrotate.d/discord-bot
   ```
   
   添加以下内容：
   ```
   /var/log/discord-bot.log {
       daily
       rotate 7
       compress
       delaycompress
       missingok
       notifempty
       create 644 你的用户名 你的用户组
   }
   ```

### 6. 性能监控

1. 查看资源使用情况：
   ```bash
   top -u 你的用户名
   # 或
   htop  # 需要先安装：sudo apt install htop
   ```

2. 查看磁盘使用情况：
   ```bash
   df -h
   du -sh /项目目录/*
   ```

### 7. 故障排除

1. 检查网络连接：
   ```bash
   ping discord.com
   curl -I https://discord.com
   ```

2. 检查进程状态：
   ```bash
   ps aux | grep python
   # 或
   pgrep -f bot.py
   ```

3. 检查端口占用：
   ```bash
   sudo netstat -tulpn | grep python
   ```

4. 检查系统日志：
   ```bash
   sudo tail -f /var/log/syslog
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
