# PythonAnywhere 部署指南

本指南详细说明如何在 PythonAnywhere 上部署 Yunhu-UserAlive 项目。

## 概述

由于 PythonAnywhere Web 应用不支持后台线程和 WebSocket 长连接，我们需要将应用拆分为两部分：

1. **Web 应用**: 仅提供 Web 控制台界面（Flask + Gunicorn）
2. **Always-on 任务**: 运行 WebSocket 客户端和定时任务

## 前置要求

- PythonAnywhere 账户（免费或付费）
- Python 3.9+ 版本
- 基本的 Git 使用知识

## 部署步骤

### 步骤 1: 创建虚拟环境

1. 登录 PythonAnywhere
2. 进入 **"Consoles"** 标签页
3. 创建一个新的 **Bash Console**
4. 运行以下命令：

```bash
# 创建虚拟环境
mkvirtualenv --python=/usr/bin/python3.9 yunhu-useralive

# 验证虚拟环境
which python  # 应该显示虚拟环境路径
```

### 步骤 2: 克隆代码

```bash
# 创建项目目录
cd ~
mkdir Yunhu-UserAlive
cd Yunhu-UserAlive

# 克隆代码（或上传代码）
# 如果使用 Git:
# git clone <your-repo-url> .
```

### 步骤 3: 安装依赖

```bash
# 确保在虚拟环境中
workon yunhu-useralive

# 安装依赖
pip install -r requirements.txt

# 验证安装
python -c "import flask; print('Flask:', flask.__version__)"
python -c "import websocket; print('websocket-client:', websocket.__version__)"
```

### 步骤 4: 配置环境变量

1. 在 PythonAnywhere 进入 **"Web"** 标签页
2. 滚动到 **"Environment variables"** 部分
3. 添加以下环境变量：

```bash
# 必需配置
MASTER_PASSWORD=your-secure-password-at-least-8-chars
ENCRYPTION_SALT=random-salt-string
FLASK_SECRET_KEY=random-secret-key-for-flask

# 路径配置（替换 yourusername 为你的用户名）
DATABASE_PATH=/home/yourusername/Yunhu-UserAlive/data/yunhu_useralive.db
LOG_FILE=/home/yourusername/Yunhu-UserAlive/logs/app.log

# PythonAnywhere 标记
PYTHONANYWHERE=true
```

4. 保存配置

### 步骤 5: 初始化数据库

```bash
# 在 Bash Console 中运行
cd /home/yourusername/Yunhu-UserAlive

# 创建数据目录
mkdir -p data logs

# 运行初始化脚本（如果需要创建用户）
# python init_user_example.py

# 或运行迁移脚本（如果有数据库更新）
# python migrate_add_weekdays.py
# python migrate_add_farewell_message.py
```

### 步骤 6: 配置 Web 应用

1. 在 **"Web"** 标签页，点击 **"Add a new web app"**
2. 选择 **"Manual configuration"**
3. 选择 Python 版本（3.9+）
4. 配置以下内容：

#### 6.1 配置 Virtualenv

```
Virtualenv: /home/yourusername/.virtualenvs/yunhu-useralive
```

#### 6.2 配置 WSGI 文件

点击 **"WSGI configuration file"** 链接，编辑内容为：

```python
import sys

# 添加项目目录到 Python 路径
path = '/home/yourusername/Yunhu-UserAlive'
if path not in sys.path:
    sys.path.insert(0, path)

# 设置环境
import os
os.environ.setdefault('PYTHONANYWHERE', 'true')

# 导入 WSGI 应用
from wsgi import app as application

# Gunicorn 配置（在进程配置中设置）
```

**重要**: 将 `yourusername` 替换为你的 PythonAnywhere 用户名。

#### 6.3 配置 Worker

```
Number of workers: 1
Worker timeout (seconds): 300
```

### 步骤 7: 配置 Always-on 任务

1. 进入 **"Tasks"** 标签页
2. 点击 **"Set up a new task"**
3. 配置任务：

```
Description: Yunhu-UserAlive WebSocket & Scheduler
Command: /home/yourusername/.virtualenvs/yunhu-useralive/bin/python /home/yourusername/Yunhu-UserAlive/always_on.py
Schedule: Every 5 minutes
Minute: */5
Hour: *
Day of week: *
```

4. 点击 **"Create task"**

### 步骤 8: 测试部署

#### 8.1 测试 Web 应用

1. 在 **"Web"** 标签页点击 **"Reload"**
2. 访问你的 PythonAnywhere 网站地址
3. 应该能看到登录页面

#### 8.2 测试 Always-on 任务

1. 检查 Always-on 任务日志：

```bash
# 在 Bash Console 中
tail -f /home/yourusername/Yunhu-UserAlive/logs/app.log
```

2. 应该看到类似输出：

```
2026-04-05 10:00:00 - INFO - ============================================================
2026-04-05 10:00:00 - INFO - Yunhu-UserAlive Always-on 任务启动
2026-04-05 10:00:01 - INFO - ✓ 登录成功! 用户 ID: 123456
2026-04-05 10:00:02 - INFO - ✓ WebSocket 连接成功
2026-04-05 10:00:03 - INFO - ✓ 定时任务已启动
```

### 步骤 9: 验证功能

1. **登录 Web 控制台**
   - 使用管理员账号登录
   - 检查仪表板显示的状态

2. **测试 WebSocket**
   - 在 Web 控制台检查 WebSocket 连接状态
   - 应该显示 "已连接"

3. **测试定时签到**
   - 等待到下一个凌晨 00:00
   - 或手动触发测试（通过代码修改时间）

4. **测试消息回复**
   - 在云湖私聊中 @ 机器人
   - 应该收到文章链接回复

## 常见问题

### 问题 1: Web 应用无法访问

**症状**: 访问网站显示 500 错误

**解决方案**:
```bash
# 检查错误日志
tail -f /var/log/www.yourusername.pythonanywhere.com.error.log

# 检查 WSGI 配置
# 确保路径和模块名正确
```

### 问题 2: Always-on 任务失败

**症状**: 任务日志显示错误

**解决方案**:
```bash
# 检查应用日志
tail -f /home/yourusername/Yunhu-UserAlive/logs/app.log

# 常见原因:
# 1. 数据库路径错误
# 2. 环境变量未设置
# 3. 虚拟环境路径错误
```

### 问题 3: WebSocket 连接失败

**症状**: Always-on 日志显示 "WebSocket 连接超时"

**解决方案**:
```bash
# 检查网络连接
# 检查 Token 是否有效
# 检查 PythonAnywhere 的网络限制

# 可以在 always_on.py 中增加调试日志
```

### 问题 4: 定时任务不执行

**症状**: 凌晨 00:00 没有签到

**解决方案**:
```bash
# 检查 Always-on 任务是否运行
# 在 Tasks 标签页查看任务状态

# 检查托管时间配置
# 在 Web 控制台设置页面检查
```

### 问题 5: 日志文件无法写入

**症状**: 日志显示 "无法创建文件日志处理器"

**解决方案**:
```bash
# 检查日志目录权限
ls -la /home/yourusername/Yunhu-UserAlive/logs

# 修复权限
chmod 755 /home/yourusername/Yunhu-UserAlive/logs
```

## 监控和维护

### 查看日志

```bash
# Web 应用日志
tail -f /var/log/www.yourusername.pythonanywhere.com.error.log

# 应用日志
tail -f /home/yourusername/Yunhu-UserAlive/logs/app.log
```

### 检查资源使用

在 PythonAnywhere 控制台：
- **"Web"** 标签页: 查看 CPU 和内存使用
- **"Tasks"** 标签页: 查看 Always-on 任务状态

### 更新代码

```bash
# 拉取最新代码
cd /home/yourusername/Yunhu-UserAlive
git pull origin main

# 重新加载 Web 应用
# 在 Web 标签页点击 "Reload"

# Always-on 任务会自动重启（5分钟后）
```

### 数据库备份

```bash
# 备份数据库
cp /home/yourusername/Yunhu-UserAlive/data/yunhu_useralive.db \
   /home/yourusername/backup/yunhu_useralive_$(date +%Y%m%d).db

# 定期备份（可以添加到计划任务）
```

## 性能优化

### 减少资源占用

1. **调整 Always-on 任务频率**
   - 改为每 10 分钟运行一次
   - 减少 WebSocket 重连次数

2. **优化数据库查询**
   - 启用查询缓存（已实现）
   - 使用索引（已配置）

3. **调整日志级别**
   - 生产环境使用 INFO 级别
   - 开发时使用 DEBUG 级别

### 免费账户限制

PythonAnywhere 免费账户的限制：

- CPU 时间: 每天 2-3 小时
- 内存: 512 MB
- 带宽: 无限制
- Always-on 任务: 1 个

**建议**:
- 使用付费账户获得更多资源
- 优化代码减少 CPU 使用
- 使用数据库缓存减少查询

## 安全建议

1. **使用强密码**
   - MASTER_PASSWORD 至少 16 字符
   - 包含大小写字母、数字、特殊字符

2. **定期更新 Token**
   - 修改 Token 刷新间隔（在 `api_client.py`）

3. **限制访问**
   - 使用 PythonAnywhere 的 IP 限制功能
   - 添加 Web 应用密码保护

4. **备份重要数据**
   - 定期备份数据库
   - 备份环境变量配置

## 下一步

- [ ] 配置域名（使用自己的域名）
- [ ] 设置 HTTPS（PythonAnywhere 提供免费 SSL）
- [ ] 配置监控告警（使用 Uptime Robot）
- [ ] 设置定期备份（使用 Cron 任务）

## 参考资料

- [PythonAnywhere 文档](https://help.pythonanywhere.com/)
- [Flask 部署指南](https://flask.palletsprojects.com/en/latest/deploying/)
- [项目 README](../README.md)
- [部署通用指南](../DEPLOYMENT.md)

## 支持

如有问题，请：
1. 查看日志文件
2. 检查本指南的常见问题部分
3. 在 GitHub 提交 Issue
