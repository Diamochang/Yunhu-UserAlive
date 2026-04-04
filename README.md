# 云湖保活用户机器人软件

一个独立的云湖自动保活用户机器人软件,支持定时签到、`@`自动回复、加密住址分享、电子终别标记和 Web 控制台管理。目前的开发版本为 Vibe Coding,后续会人工测试。

## 功能特性

✅ **自动签到**: 每日凌晨 00:00-00:05 随机时间执行 HXBOT 普通签到、鹿管签到和有一城群聊签到  
✅ **@自动回复**: 被 @ 时自动发送预设的云湖文章内链(Markdown 格式)  
✅ **加密住址分享**: 为信任好友设置点对点加密住址信息,通过关键词"住址"触发  
✅ **电子终别标记**: 局部/全局标记,提醒好友保持联系,支持延时自动开启  
✅ **Web 控制台**: 查看运行状态、调整配置、手动控制开关,敏感操作需 TOTP 验证  

## 技术栈

- **后端**: Python 3.9+
- **Web 框架**: Flask
- **WebSocket**: websocket-client
- **数据库**: SQLite (兼容 LiteFS)
- **加密**: cryptography (Fernet + PBKDF2)
- **2FA**: pyotp (TOTP)
- **定时任务**: APScheduler

## 安装步骤

### 1. 克隆项目

```bash
cd /home/diamochang/文档/Projects/Python/Yunhu-UserAlive
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `.env.example` 为 `.env`:

```bash
cp .env.example .env
```

编辑 `.env` 文件,填写配置:

```env
MASTER_PASSWORD=your-strong-password-here
ENCRYPTION_SALT=generate-random-salt-once
FLASK_SECRET_KEY=change-this-in-production
DATABASE_PATH=yunhu_useralive.db
```

**重要**: 
- `MASTER_PASSWORD` 至少 8 个字符,用于加密敏感数据
- `ENCRYPTION_SALT` 首次启动后不要修改,否则无法解密已有数据

### 4. 初始化用户

创建 `init_user.py` 文件:

```python
from database.db_manager import DatabaseManager
from auth.crypto import CryptoManager

db = DatabaseManager()
crypto = CryptoManager()

# 加密邮箱和密码
email_encrypted = crypto.encrypt("your-email@example.com")
password_encrypted = crypto.encrypt("your-cloudlake-password")

# 添加用户
user_id = db.add_user(
    email=email_encrypted,
    password_encrypted=password_encrypted,
    device_id="UserAlive",  # 可自定义
    platform="linux"
)

print(f"用户已添加,ID: {user_id}")

# 可选:添加示例文章链接
db.add_article_link(user_id, "在线时间表", "yunhu://post-detail?id=31628")
print("示例文章已添加")
```

运行初始化脚本:

```bash
python init_user.py
```

### 5. 启动程序

```bash
python app.py
```

程序启动后会:
1. 连接云湖 WebSocket
2. 启动定时任务调度器
3. 启动 Web 控制台 (http://localhost:5000)

## 使用指南

### Web 控制台

访问 http://localhost:5000,使用邮箱和密码登录。

**仪表板功能**:
- 查看 WebSocket 连接状态
- 查看定时任务运行状态
- 查看最后签到时间
- 手动触发签到

**设置页面**:
- 添加文章链接(用于 @ 自动回复)
- 添加信任好友及加密住址
- 设置电子终别自动开启延迟

### 添加信任好友

在 Web 控制台设置页面:
1. 输入好友的云湖 ID
2. 输入备注名(可选)
3. 输入要加密的住址信息
4. 点击"添加"

当好友私聊发送"住址"时,机器人会自动回复加密的住址信息。

### 电子终别标记

**局部标记**: 针对特定好友启用,当该好友查询住址时会显示提醒消息。

**全局标记**: 对所有好友生效,可通过以下方式开启:
- 手动在数据库中设置
- 设置自动开启延迟:用户最后一次访问控制台后指定时间自动开启

关闭全局标记需要密码验证。

### 定时签到

每日凌晨 00:00 触发,实际执行时间会随机延迟 0-5 分钟:
1. 向 HXBOT (ID: 45059971) 发送 `/签到`
2. 向 HXBOT 发送 `/鹿`
3. 向有一城群聊 (ID: 679137839) 发送"签到"/"打卡"/"冒泡"之一

签到结果会记录到数据库,可在日志中查看。

## 常见问题

### Q: 如何修改签到时间?

A: 编辑 `scheduler/tasks.py`,修改 `CronTrigger` 的参数:

```python
self.scheduler.add_job(
    func=self.daily_checkin,
    trigger=CronTrigger(hour=0, minute=0),  # 修改这里
    ...
)
```

### Q: WebSocket 连接失败怎么办?

A: 检查以下几点:
1. 网络连接是否正常
2. 邮箱和密码是否正确
3. Token 是否过期(程序会自动重新登录)
4. 查看 `logs/app.log` 获取详细错误信息

### Q: 如何备份数据?

A: 备份以下文件:
- `yunhu_useralive.db` (数据库文件)
- `.env` (包含加密密钥)

**重要**: 丢失 `.env` 中的 `MASTER_PASSWORD` 或 `ENCRYPTION_SALT` 将导致无法解密数据!

### Q: 如何重置 TOTP?

A: 目前需要通过数据库操作:

```sql
UPDATE totp_secrets SET is_active = 0 WHERE user_id = 1;
```

然后在应用中重新配置 TOTP。

## 安全注意事项

⚠️ **重要安全提示**:

1. **保护主密码**: `MASTER_PASSWORD` 是加密的核心,切勿泄露
2. **备份盐值**: `ENCRYPTION_SALT` 丢失将导致所有加密数据无法恢复
3. **HTTPS**: 生产环境务必启用 HTTPS
4. **防火墙**: 限制 Web 控制台的访问 IP
5. **定期更新**: 保持依赖库更新以修复安全漏洞

## 许可证

[GNU Affero 通用公共许可证第三版](LICENSE)或任何以后版本。
