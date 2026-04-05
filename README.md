# 云湖保活用户机器人软件

一个独立的云湖自动保活用户机器人软件,支持定时签到、`@`自动回复、加密住址分享、电子终别标记和 Web 控制台管理。目前的开发版本为 Vibe Coding,后续会人工测试。

## 功能特性

✅ **自动签到**: 每日凌晨 00:00 准时执行 HXBOT 普通签到、鹿管签到和有一城群聊签到  
✅ **按星期托管**: 可设置每周哪些天启用自动托管,灵活控制运行时间  
✅ **@自动回复**: 被 @ 时自动发送预设的云湖文章内链(Markdown 格式)  
✅ **加密住址分享**: 使用 OpenPGP 为信任好友设置点对点加密住址信息,通过关键词“住址”触发  
✅ **电子终别标记**: 局部/全局标记,提醒好友保持联系,支持延时自动开启  
✅ **Web 控制台**: Bootstrap 5 现代化界面,查看运行状态、调整配置、手动控制开关

## 技术栈

- **后端**: Python 3.9+
- **Web 框架**: Flask
- **WebSocket**: websocket-client
- **数据库**: SQLite (兼容 LiteFS)
- **加密**: cryptography (Fernet + PBKDF2), OpenPGP (GnuPG)
- **2FA**: pyotp (TOTP)
- **定时任务**: APScheduler
- **消息序列化**: Protocol Buffers (支持 JSON 降级)

## 项目结构

详见 [项目结构文档](docs/项目结构.md)

**核心模块**:
- `auth/` - 认证和加密
- `database/` - 数据库管理
- `yunhu/` - 云湖 API 客户端
- `scheduler/` - 定时任务
- `web/` - Web 控制台
- `proto/` - ProtoBuf 支持

## 安装步骤

### 快速开始（3 步）

```bash
# 1. 复制配置文件
cp config_local.py.example config.py

# 2. 运行初始化向导
python init.py

# 3. 启动应用
python app.py
```

初始化向导会自动处理：
- ✅ 配置验证
- ✅ 数据库创建
- ✅ 云湖账户配置
- ✅ 数据迁移（如果需要）

访问控制台: http://localhost:5000

### 详细步骤

#### 1. 安装依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置系统

编辑 `config.py`，设置必需的配置：

```python
# 必需配置（首次设置后不要修改）
MASTER_PASSWORD = "your-secure-password-at-least-8-chars"
ENCRYPTION_SALT = "your-random-salt"
FLASK_SECRET_KEY = "your-flask-secret"

# 部署环境
DEPLOYMENT_ENV = "local"  # 或 "pythonanywhere"
```

**生成安全密钥**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(16))"  # MASTER_PASSWORD
python -c "import secrets; print(secrets.token_hex(16))"     # ENCRYPTION_SALT
python -c "import secrets; print(secrets.token_urlsafe(32))"  # FLASK_SECRET_KEY
```

#### 3. 运行初始化

如需启用高性能的 ProtoBuf 消息序列化:

```bash
# 安装 protobuf 编译器
sudo apt-get install protobuf-compiler  # Debian/Ubuntu
# 或
brew install protobuf  # macOS

# 编译 ProtoBuf 文件
cd proto
bash compile.sh
cd ..
```

**注意**: 如果不编译 ProtoBuf，程序会自动使用 JSON 格式，功能完全相同。

详见 [ProtoBuf 使用指南](docs/ProtoBuf_使用指南.md)

#### 5. 启动应用

### 4. 配置环境变量

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

### 5. (可选) 运行数据库迁移

如果已有旧版本数据库,需要运行迁移脚本:

```bash
python migrate_add_weekdays.py
```

这会:
- 添加 `takeover_weekdays` 字段
- 将时间字段从 TIME 改为 TEXT (YYYY/MM/DD HH:MM:SS)

**注意**: 如果是全新安装,可以跳过此步骤。

```bash
python init.py
```

初始化向导会引导你完成：
- 验证配置文件
- 初始化数据库
- 配置云湖账户（邮箱和密码）
- 执行数据库迁移（如果需要）
- 生成随机密钥（可选）

#### 4. (可选) 编译 ProtoBuf
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

```bash
python app.py
```

服务器将在 `http://localhost:5000` 启动。

使用初始化时配置的邮箱和密码登录。

## 配置说明

### 统一配置文件

所有配置都在 `config.py` 文件中，包括：

**必需配置**（首次设置后不要修改）：
- `MASTER_PASSWORD` - 加密主密码（至少 8 字符）
- `ENCRYPTION_SALT` - 加密盐值
- `FLASK_SECRET_KEY` - Flask 会话密钥

**环境配置**：
- `DEPLOYMENT_ENV` - 部署环境（"local" 或 "pythonanywhere"）
- `DATABASE_PATH` - 数据库路径
- `LOG_FILE` - 日志文件路径

**功能配置**：
- `YUNHU_API_BASE_URL` - 云湖 API 地址
- `YUNHU_WS_URL` - WebSocket 地址
- `CHECKIN_BOT_ID` - 签到机器人 ID
- `CHECKIN_GROUP_ID` - 签到群聊 ID

详见 [快速开始指南](docs/快速开始.md)

```bash
python app.py
```

程序启动后会:
1. 连接云湖 WebSocket
2. 启动定时任务调度器
3. 启动 Web 控制台 (http://localhost:5000)

## 使用指南

### Web 控制台

### PythonAnywhere 云部署

对于需要 24/7 稳定运行的生产环境,推荐使用 PythonAnywhere 云平台。

**快速部署**:

```bash
# 1. 修改配置文件
# 在 config.py 中设置:
DEPLOYMENT_ENV = "pythonanywhere"

# 2. 在 PythonAnywhere 上运行初始化
python init.py

# 3. 配置 Web 应用（使用 wsgi.py）
# 4. 配置 Always-on 任务（使用 always_on.py）
```

详细文档:
- [快速开始指南](docs/快速开始.md)
- [PythonAnywhere 快速开始](docs/PythonAnywhere快速开始.md)
- [PythonAnywhere 部署指南](docs/PythonAnywhere部署指南.md)
- [逻辑检查与适配总结](LOGIC_CHECK_SUMMARY.md)

**架构说明**:
- **Web 应用**: 提供控制台界面（Flask + Gunicorn）
- **Always-on 任务**: 运行 WebSocket 和定时任务
- 两个进程共享 SQLite 数据库

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
3. **使用 OpenPGP 加密住址信息** (详见 [OpenPGP 加密住址使用指南](docs/OpenPGP_加密住址使用指南.md))
4. (可选) 勾选“启用局部‘电子终别’标记”
5. 点击“添加”

当好友私聊发送“住址”时,机器人会自动回复加密的住址信息和电子终别提醒(如果启用)。

## Web 控制台

### ✨ Bootstrap 5 现代化界面

v1.2.0 版本采用 Bootstrap 5 完全重构了 Web 控制台:

**主要特性**:
- 📱 **响应式设计**: 完美支持桌面、平板和手机
- 🎨 **现代化 UI**: 卡片式布局,清晰的视觉层次
- 🔔 **实时状态**: WebSocket、定时任务、ProtoBuf 状态实时更新
- ⚙️ **便捷配置**: 直观的表单界面,即时保存
- 🔒 **安全登录**: 邮箱+密码认证,会话管理

**页面结构**:
```
web/templates/
├── base.html          # 基础布局(导航栏、页脚)
├── login.html         # 登录页面
├── dashboard.html     # 仪表板(状态监控)
└── settings.html      # 设置页面(托管、好友、文章)
```

**访问方式**:
```bash
python main.py
# 浏览器访问: http://localhost:5000
```

详细使用说明请查看 [Web 界面使用指南](docs/Web_界面使用指南.md)

### 电子终别标记

**局部标记**: 针对特定好友启用,当该好友查询住址时会显示提醒消息。

**全局标记**: 对所有好友生效,可通过以下方式开启:
- 手动在数据库中设置
- 设置自动开启延迟:用户最后一次访问控制台后指定时间自动开启

关闭全局标记需要密码验证。

### 定时签到

每日凌晨 00:00 准时触发(仅在托管时间内执行):
1. 向 HXBOT (ID: 45059971) 发送 `/签到`
2. 向 HXBOT 发送 `/鹿`
3. 向有一城群聊 (ID: 679137839) 发送“签到”/“打卡”/“冒泡”之一

签到结果会记录到数据库,可在日志中查看。

**按星期托管设置**:
在仪表板中可以设置每周哪些天启用自动托管,例如:
- 仅工作日(周一至周五)
- 仅周末(周六、周日)
- 自定义组合

**时间格式**: 使用 `YYYY/MM/DD HH:MM:SS` 格式,例如 `2024/01/01 00:00:00`

只有当前时间在托管时间范围内且当天是启用的星期时,才会执行签到任务。

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
