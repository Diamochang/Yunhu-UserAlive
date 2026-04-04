import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """应用配置类"""
    
    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'yunhu_useralive.db')
    
    # 加密配置
    MASTER_PASSWORD = os.getenv('MASTER_PASSWORD')
    ENCRYPTION_SALT = os.getenv('ENCRYPTION_SALT', 'default-salt-change-in-production')
    
    # Flask 配置
    FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    
    # 云湖 API 配置
    YUNHU_API_BASE_URL = "https://chat-go.jwzhd.com"
    YUNHU_WS_URL = "wss://chat-ws-go.jwzhd.com/ws"
    
    # 签到配置
    CHECKIN_BOT_ID = "45059971"  # HXBOT 机器人 ID
    CHECKIN_GROUP_ID = "679137839"  # 有一城群聊 ID
    CHECKIN_DELAY_MIN = 0  # 最小延迟(秒)
    CHECKIN_DELAY_MAX = 300  # 最大延迟(秒, 5分钟)
    
    # 日志配置
    LOG_FILE = 'logs/app.log'
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 5
    
    @classmethod
    def validate(cls):
        """验证必需的配置项"""
        if not cls.MASTER_PASSWORD:
            raise ValueError("MASTER_PASSWORD 环境变量未设置")
        if len(cls.MASTER_PASSWORD) < 8:
            raise ValueError("MASTER_PASSWORD 长度至少为 8 个字符")
