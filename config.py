# ==========================================
# Yunhu-UserAlive 统一配置文件
# ==========================================
# 
# 这是项目的唯一配置文件，包含所有必要的配置项
# 
# 使用方法:
# 1. 复制此文件为 config.py
# 2. 根据你的环境修改配置
# 3. 运行 python init.py 进行初始化
# 
# ==========================================

# ==================== 加密配置 ====================
# ⚠️ 重要: 这些配置用于加密敏感数据，首次设置后不要修改！
# 修改后会导致无法解密已有数据（如邮箱、密码）

# 加密主密码（至少 8 个字符）
# 建议使用随机字符串，例如: python -c "import secrets; print(secrets.token_urlsafe(16))"
MASTER_PASSWORD = "change-this-to-a-secure-password-at-least-8-chars"

# 加密盐值（用于增加加密强度）
# 首次启动后不要修改！
# 建议使用随机字符串，例如: python -c "import secrets; print(secrets.token_hex(16))"
ENCRYPTION_SALT = "change-this-to-a-random-salt"

# Flask 会话密钥（用于加密用户会话）
# 建议使用随机字符串
FLASK_SECRET_KEY = "change-this-to-a-random-flask-secret"

# ==================== 数据库配置 ====================
# 数据库文件路径

# 本地开发使用相对路径
DATABASE_PATH = "data/yunhu_useralive.db"

# 如果在 PythonAnywhere 部署，使用绝对路径:
# DATABASE_PATH = "/home/yourusername/Yunhu-UserAlive/data/yunhu_useralive.db"

# ==================== 日志配置 ====================
# 日志文件路径

# 本地开发使用相对路径
LOG_FILE = "logs/app.log"

# 如果在 PythonAnywhere 部署，使用绝对路径:
# LOG_FILE = "/home/yourusername/Yunhu-UserAlive/logs/app.log"

# 日志文件最大大小（字节，10MB）
LOG_MAX_BYTES = 10 * 1024 * 1024

# 日志文件备份数量
LOG_BACKUP_COUNT = 5

# ==================== 云湖 API 配置 ====================
# 云湖 API 基础 URL
YUNHU_API_BASE_URL = "https://chat-go.jwzhd.com"

# WebSocket URL
YUNHU_WS_URL = "wss://chat-ws-go.jwzhd.com/ws"

# ==================== 签到配置 ====================
# HXBOT 机器人 ID（用于签到）
CHECKIN_BOT_ID = "45059971"

# 有一城群聊 ID（用于签到）
CHECKIN_GROUP_ID = "679137839"

# 签到延迟范围（秒）
# CHECKIN_DELAY_MIN = 0 表示准时执行
# CHECKIN_DELAY_MAX = 300 表示最多延迟 5 分钟
CHECKIN_DELAY_MIN = 0
CHECKIN_DELAY_MAX = 300

# ==================== 部署环境 ====================
# 检测运行环境
# 可选值: "local"（本地开发）或 "pythonanywhere"（云端部署）

# 本地开发
DEPLOYMENT_ENV = "local"

# PythonAnywhere 部署
# DEPLOYMENT_ENV = "pythonanywhere"

# ==================== 云湖账户配置 ====================
# ⚠️ 注意: 这些信息将在初始化时加密存储到数据库
# 首次运行 init.py 时会提示输入

# 云湖邮箱地址
YUNHU_EMAIL = ""  # 留空，初始化时通过命令行输入

# 云湖密码
YUNHU_PASSWORD = ""  # 留空，初始化时通过命令行输入

# 设备 ID（云湖用于识别设备）
# 可以是任意唯一字符串，建议使用: python -c "import uuid; print(str(uuid.uuid4()))"
DEVICE_ID = ""  # 留空，自动生成

# 平台标识
# 可选值: "windows", "macos", "android", "linux", "ios", "fuchsia", "Web"
PLATFORM = "linux"

# ==================== 自动生成配置 ====================
# 以下配置由系统自动生成，无需手动修改

import os
import sys

# 自动设置工作目录为项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# 根据部署环境自动调整路径
if DEPLOYMENT_ENV == "pythonanywhere":
    # PythonAnywhere 使用绝对路径
    USERNAME = os.path.basename(os.path.expanduser("~"))
    DATABASE_PATH = DATABASE_PATH.replace(
        "data/yunhu_useralive.db",
        f"/home/{USERNAME}/Yunhu-UserAlive/data/yunhu_useralive.db"
    )
    LOG_FILE = LOG_FILE.replace(
        "logs/app.log",
        f"/home/{USERNAME}/Yunhu-UserAlive/logs/app.log"
    )

# 创建必要的目录
os.makedirs(os.path.dirname(DATABASE_PATH) or ".", exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE) or ".", exist_ok=True)

# ==================== 配置验证 ====================
def validate_config():
    """验证配置是否有效"""
    errors = []
    
    # 检查必需的配置
    if not MASTER_PASSWORD or len(MASTER_PASSWORD) < 8:
        errors.append("MASTER_PASSWORD 必须至少 8 个字符")
    
    if not ENCRYPTION_SALT:
        errors.append("ENCRYPTION_SALT 不能为空")
    
    if not FLASK_SECRET_KEY:
        errors.append("FLASK_SECRET_KEY 不能为空")
    
    # 检查部署环境
    if DEPLOYMENT_ENV not in ["local", "pythonanywhere"]:
        errors.append("DEPLOYMENT_ENV 必须是 'local' 或 'pythonanywhere'")
    
    if errors:
        raise ValueError("\n".join(errors))
    
    return True

# ==================== 导出配置 ====================
# 以下变量会被其他模块导入使用
__all__ = [
    # 加密配置
    "MASTER_PASSWORD",
    "ENCRYPTION_SALT",
    "FLASK_SECRET_KEY",
    
    # 数据库配置
    "DATABASE_PATH",
    
    # 日志配置
    "LOG_FILE",
    "LOG_MAX_BYTES",
    "LOG_BACKUP_COUNT",
    
    # API 配置
    "YUNHU_API_BASE_URL",
    "YUNHU_WS_URL",
    
    # 签到配置
    "CHECKIN_BOT_ID",
    "CHECKIN_GROUP_ID",
    "CHECKIN_DELAY_MIN",
    "CHECKIN_DELAY_MAX",
    
    # 部署环境
    "DEPLOYMENT_ENV",
    
    # 云湖账户配置
    "YUNHU_EMAIL",
    "YUNHU_PASSWORD",
    "DEVICE_ID",
    "PLATFORM",
    
    # 项目根目录
    "PROJECT_ROOT",
]
