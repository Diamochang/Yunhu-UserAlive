# 快速启动指南

## 第一步:安装依赖

```bash
pip install -r requirements.txt
```

## 第二步:配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件:

```env
MASTER_PASSWORD=设置一个强密码(至少8位)
ENCRYPTION_SALT=可以保持默认或生成随机字符串
FLASK_SECRET_KEY=生成一个随机密钥
DATABASE_PATH=yunhu_useralive.db
```

**重要**: `MASTER_PASSWORD` 和 `ENCRYPTION_SALT` 一旦设置后不要修改,否则无法解密数据!

## 第三步:初始化用户

编辑 `init_user_example.py`,修改以下信息:

```python
EMAIL = "your-email@example.com"  # 你的云湖邮箱
PASSWORD = "your-cloudlake-password"  # 你的云湖密码
DEVICE_ID = "my-device-001"  # 自定义设备ID
```

运行初始化脚本:

```bash
python init_user_example.py
```

## 第四步:启动程序

```bash
python app.py
```

程序启动后会显示:

```
============================================================
云湖保活用户机器人已成功启动!
Web 控制台: http://localhost:5000
按 Ctrl+C 停止运行
============================================================
```

## 第五步:访问 Web 控制台

浏览器打开: http://localhost:5000

使用云湖邮箱和密码登录。

## 常用操作

### 添加文章链接(用于@自动回复)

在 Web 控制台 → 设置页面 → 添加文章链接

示例:
- 标题: 在线时间表
- URL: yunhu://post-detail?id=31628

### 添加信任好友(用于加密住址分享)

在 Web 控制台 → 设置页面 → 添加信任好友

填写:
- 好友云湖 ID
- 备注名(可选)
- 住址信息(会被加密存储)

当好友私聊发送"住址"时,机器人会自动回复加密的住址。

### 手动触发签到

在 Web 控制台仪表板 → 点击"立即签到"按钮

### 查看日志

```bash
tail -f logs/app.log
```

## 故障排查

### 问题:登录失败

检查:
1. 邮箱和密码是否正确
2. 网络连接是否正常
3. 查看 `logs/app.log` 获取详细错误信息

### 问题:WebSocket 连接失败

检查:
1. Token 是否过期(程序会自动重新登录)
2. 防火墙是否阻止了 WebSocket 连接
3. 云湖服务器是否正常

### 问题:无法启动

检查:
1. 是否已安装所有依赖:`pip install -r requirements.txt`
2. `.env` 文件是否存在且配置正确
3. Python 版本是否 >= 3.9

## 停止程序

按 `Ctrl+C` 即可安全停止。

## 后台运行(可选)

使用 nohup:

```bash
nohup python app.py > output.log 2>&1 &
```

使用 screen:

```bash
screen -S yunhu
python app.py
# 按 Ctrl+A,然后按 D 退出 screen
# 恢复: screen -r yunhu
```

## 备份数据

定期备份以下文件:
- `yunhu_useralive.db` (数据库)
- `.env` (包含加密密钥)

**警告**: 丢失 `.env` 将导致无法解密数据!

---

祝使用愉快! 🎉
