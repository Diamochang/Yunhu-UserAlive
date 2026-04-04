"""
云湖保活用户机器人 - 主应用入口
"""

import os
import sys
import logging
import threading
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
def setup_logging():
    """设置日志系统"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 确保 logs 目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console_handler)


def main():
    """主函数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("云湖保活用户机器人启动中...")
    logger.info("=" * 60)
    
    # 验证配置
    try:
        from config import Config
        Config.validate()
        logger.info("配置验证通过")
    except ValueError as e:
        logger.error(f"配置错误: {str(e)}")
        logger.error("请复制 .env.example 为 .env 并填写正确的配置")
        sys.exit(1)
    
    # 初始化数据库
    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    db.init_db()
    logger.info("数据库初始化完成")
    
    # 检查是否有用户配置
    users = db.get_all_users()
    if not users:
        logger.warning("数据库中未找到用户配置")
        logger.info("请使用以下代码添加第一个用户:")
        logger.info("""
from database.db_manager import DatabaseManager
from auth.crypto import CryptoManager

db = DatabaseManager()
crypto = CryptoManager()

# 加密邮箱和密码
email_encrypted = crypto.encrypt("your-email@example.com")
password_encrypted = crypto.encrypt("your-password")

# 添加用户
db.add_user(
    email="your-email@example.com",
    password_encrypted=password_encrypted,
    device_id="your-device-id-123",
    platform="windows"
)
        """)
        logger.info("添加用户后请重新启动程序")
        sys.exit(1)
    
    # 取第一个用户
    user = users[0]
    logger.info(f"使用用户: {user['email']}")
    
    # 初始化工具类
    from auth.crypto import CryptoManager
    crypto = CryptoManager()
    
    # 解密密码
    try:
        password = crypto.decrypt(user['password_encrypted'])
        email = crypto.decrypt(user['email'])
    except Exception as e:
        logger.error(f"解密失败: {str(e)}")
        sys.exit(1)
    
    # 初始化 API 客户端并登录
    from yunhu.api_client import YunhuAPIClient
    api_client = YunhuAPIClient()
    
    logger.info("正在登录云湖...")
    login_result = api_client.email_login(
        email=email,
        password=password,
        device_id=user['device_id'],
        platform=user['platform']
    )
    
    if not login_result['success']:
        logger.error(f"登录失败: {login_result.get('error')}")
        sys.exit(1)
    
    logger.info(f"✓ 登录成功! 用户 ID: {api_client.user_id}")
    
    # 更新数据库中的 Token
    db.update_user_token(user['id'], api_client.token, api_client.user_id)
    
    # 初始化 WebSocket 客户端
    from yunhu.websocket_client import YunhuWebSocketClient
    ws_client = YunhuWebSocketClient(
        user_id=api_client.user_id,
        token=api_client.token,
        device_id=user['device_id'],
        platform=user['platform']
    )
    
    # 初始化消息处理器
    from yunhu.message_handler import MessageHandler
    message_handler = MessageHandler(ws_client, db, crypto)
    ws_client.message_callback = message_handler.handle_message
    
    # 在后台线程启动 WebSocket 连接
    logger.info("正在连接 WebSocket...")
    ws_thread = threading.Thread(target=ws_client.connect, daemon=True)
    ws_thread.start()
    
    # 等待 WebSocket 连接
    import time
    for i in range(10):
        if ws_client.connected:
            logger.info("✓ WebSocket 连接成功")
            break
        time.sleep(1)
    else:
        logger.warning("WebSocket 连接超时,将继续尝试...")
    
    # 启动定时任务
    from scheduler.tasks import TaskScheduler
    scheduler = TaskScheduler(ws_client, db)
    scheduler.start()
    logger.info("✓ 定时任务已启动")
    
    # 启动 Flask Web 控制台
    from web.routes import create_app
    app = create_app(scheduler=scheduler, ws_client=ws_client)
    
    logger.info("=" * 60)
    logger.info("云湖保活用户机器人已成功启动!")
    logger.info("Web 控制台: http://localhost:5000")
    logger.info("按 Ctrl+C 停止运行")
    logger.info("=" * 60)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("\n正在关闭...")
        scheduler.stop()
        ws_client.disconnect()
        logger.info("已安全退出")


if __name__ == '__main__':
    main()
