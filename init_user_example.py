"""
用户初始化脚本示例
使用前请修改邮箱、密码和设备 ID
"""

from database.db_manager import DatabaseManager
from auth.crypto import CryptoManager

def init_user():
    """初始化第一个用户"""
    
    # 配置信息(请修改为你的实际信息)
    EMAIL = "your-email@example.com"
    PASSWORD = "your-cloudlake-password"
    DEVICE_ID = "my-device-001"
    PLATFORM = "windows"
    
    print("正在初始化用户...")
    
    # 初始化工具类
    db = DatabaseManager()
    crypto = CryptoManager()
    
    # 加密敏感信息
    email_encrypted = crypto.encrypt(EMAIL)
    password_encrypted = crypto.encrypt(PASSWORD)
    
    # 添加用户到数据库
    user_id = db.add_user(
        email=email_encrypted,
        password_encrypted=password_encrypted,
        device_id=DEVICE_ID,
        platform=PLATFORM
    )
    
    print(f"✓ 用户已添加,ID: {user_id}")
    print(f"  邮箱: {EMAIL}")
    print(f"  设备 ID: {DEVICE_ID}")
    print(f"  平台: {PLATFORM}")
    
    # 添加示例文章链接(可选)
    sample_articles = [
        {"title": "在线时间表", "url": "yunhu://post-detail?id=31628"},
        {"title": "云湖使用指南", "url": "yunhu://post-detail?id=12345"},
    ]
    
    for article in sample_articles:
        db.add_article_link(user_id, article['title'], article['url'])
        print(f"✓ 添加文章: {article['title']}")
    
    print("\n初始化完成!")
    print("现在可以运行 'python app.py' 启动程序")


if __name__ == '__main__':
    try:
        init_user()
    except Exception as e:
        print(f"错误: {str(e)}")
        print("\n请确保:")
        print("1. 已复制 .env.example 为 .env")
        print("2. 已在 .env 中配置 MASTER_PASSWORD 和 ENCRYPTION_SALT")
        print("3. 已安装所有依赖: pip install -r requirements.txt")
