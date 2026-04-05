# PythonAnywhere 快速开始指南

## 🚀 5 分钟快速部署

### 前置条件

- PythonAnywhere 账号（免费或付费）
- Git 账号（可选）

### 步骤 1: 创建虚拟环境（1 分钟）

```bash
# 在 PythonAnywhere Bash Console 中执行
mkvirtualenv --python=/usr/bin/python3.9 yunhu-useralive
workon yunhu-useralive
```

### 步骤 2: 上传代码（1 分钟）

```bash
# 方法 A: 使用 Git（推荐）
cd ~
git clone https://github.com/Diamochang/Yunhu-UserAlive.git Yunhu-UserAlive
cd Yunhu-UserAlive

# 方法 B: 使用上传文件
# 在 Files 标签页上传整个项目
```

### 步骤 3: 安装依赖（1 分钟）

```bash
cd ~/Yunhu-UserAlive
pip install -r requirements.txt
```

### 步骤 4: 设置环境变量（1 分钟）

在 **Web → Environment variables** 添加：

```bash
MASTER_PASSWORD=your-secure-password
ENCRYPTION_SALT=random-salt
FLASK_SECRET_KEY=random-secret
DATABASE_PATH=/home/YOUR_USERNAME/Yunhu-UserAlive/data/yunhu_useralive.db
LOG_FILE=/home/YOUR_USERNAME/Yunhu-UserAlive/logs/app.log
PYTHONANYWHERE=true
```

⚠️ **重要**: 将 `YOUR_USERNAME` 替换为你的 PythonAnywhere 用户名

### 步骤 5: 初始化数据库（1 分钟）

```bash
cd ~/Yunhu-UserAlive
python init_user_example.py
```

### 步骤 6: 配置 Web 应用（1 分钟）

1. **Web → Add a new web app**
2. 选择 **Manual configuration**
3. Python 版本选择 **3.12**
4. Virtualenv 设置为: `/home/YOUR_USERNAME/.virtualenvs/yunhu-useralive`
5. WSGI 配置文件编辑为:

```python
import sys
path = '/home/YOUR_USERNAME/Yunhu-UserAlive'
if path not in sys.path:
    sys.path.insert(0, path)

import os
os.environ.setdefault('PYTHONANYWHERE', 'true')

from wsgi import app as application
```

6. 点击 **Reload**

### 步骤 7: 配置 Always-on 任务（1 分钟）

在 **Tasks** 标签页创建新任务：

```
Description: Yunhu-UserAlive
Command: /home/YOUR_USERNAME/.virtualenvs/yunhu-useralive/bin/python /home/YOUR_USERNAME/Yunhu-UserAlive/always_on.py
Schedule: Every 5 minutes
```

### 步骤 8: 测试部署（1 分钟）

1. 访问你的 PythonAnywhere 网站
2. 使用创建的账号登录
3. 检查仪表板状态

## ✅ 验证清单

- [ ] Web 应用可以访问
- [ ] 可以登录成功
- [ ] 仪表板显示 WebSocket 连接状态
- [ ] Always-on 任务运行正常
- [ ] 日志文件有内容

## 📝 常用命令

### 查看日志

```bash
# 应用日志
tail -f ~/Yunhu-UserAlive/logs/app.log

# Web 错误日志
tail -f /var/log/www.YOUR_USERNAME.pythonanywhere.com.error.log
```

### 检查配置

```bash
cd ~/Yunhu-UserAlive
python check_deployment.py
```

### 重启服务

```bash
# 重启 Web 应用
# 在 Web 标签页点击 "Reload"

# 重启 Always-on 任务
# 任务会自动在 5 分钟后重启
```

## 🐛 快速修复

### 问题: Web 应用 500 错误

```bash
# 检查错误日志
tail -f /var/log/www.YOUR_USERNAME.pythonanywhere.com.error.log

# 常见原因:
# 1. 虚拟环境路径错误
# 2. WSGI 文件配置错误
# 3. 依赖未安装
```

### 问题: Always-on 任务失败

```bash
# 检查应用日志
tail -f ~/Yunhu-UserAlive/logs/app.log

# 常见原因:
# 1. 数据库路径错误
# 2. 环境变量未设置
# 3. 网络连接问题
```

### 问题: 数据库无法写入

```bash
# 检查目录权限
ls -la ~/Yunhu-UserAlive/data

# 修复权限
chmod 755 ~/Yunhu-UserAlive/data
chmod 644 ~/Yunhu-UserAlive/data/*.db
```

## 📚 更多信息

- 完整部署指南: [PythonAnywhere部署指南.md](./PythonAnywhere部署指南.md)
- 逻辑检查总结: [../LOGIC_CHECK_SUMMARY.md](../LOGIC_CHECK_SUMMARY.md)
- 项目 README: [../README.md](../README.md)

## 💡 提示

1. **用户名替换**: 所有命令中的 `YOUR_USERNAME` 需要替换为你的实际用户名
2. **日志监控**: 部署后持续监控日志文件
3. **定期检查**: 每天检查一次应用运行状态
4. **备份数据**: 定期备份数据库文件

## 🆘 需要帮助？

1. 查看日志文件寻找错误信息
2. 运行 `check_deployment.py` 检查配置
3. 查看 [常见问题](./PythonAnywhere部署指南.md#常见问题)
4. 在 GitHub 提交 Issue
