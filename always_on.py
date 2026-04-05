#!/usr/bin/env python3
"""
PythonAnywhere Always-on 任务入口
运行 WebSocket 客户端和定时任务

在 PythonAnywhere 上配置为 Always-on 任务:
1. 在 "Tasks" 标签页创建新任务
2. 命令: /home/yourusername/.virtualenvs/yunhu-useralive/bin/python /home/yourusername/Yunhu-UserAlive/always_on.py
3. 设置合适的超时时间（建议 300 秒）
4. 每 5 分钟运行一次
"""

import os
import sys
import time
import logging
import signal
from logging.handlers import RotatingFileHandler

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置日志（确保使用绝对路径）
def setup_logging():
    """设置日志系统"""
    from config import LOG_FILE, LOG_MAX_BYTES, LOG_BACKUP_COUNT
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 确保日志目录存在
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT
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

setup_logging()
logger = logging.getLogger(__name__)

# 全局变量
ws_client = None
scheduler = None
running = True

def signal_handler(signum, frame):
    """信号处理器"""
    global running
    logger.info(f"收到信号 {signum}, 准备退出...")
    running = False

def cleanup():
    """清理资源"""
    global scheduler, ws_client
    
    logger.info("正在清理资源...")
    
    if scheduler:
        try:
            scheduler.stop()
            logger.info("定时任务已停止")
        except Exception as e:
            logger.error(f"停止定时任务失败: {e}")
    
    if ws_client:
        try:
            ws_client.disconnect()
            logger.info("WebSocket 已断开")
        except Exception as e:
            logger.error(f"断开 WebSocket 失败: {e}")
    
    logger.info("资源清理完成")

def main():
    """主函数"""
    global ws_client, scheduler, running
    
    # 注册信号处理器
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("=" * 60)
    logger.info("Yunhu-UserAlive Always-on 任务启动")
    logger.info("=" * 60)
    
    try:
        # 验证配置
        from config import validate_config
        validate_config()
        logger.info("配置验证通过")
    except ValueError as e:
        logger.error(f"配置错误: {str(e)}")
        sys.exit(1)
    
    # 初始化数据库
    from database.db_manager import DatabaseManager
    db = DatabaseManager()
    db.init_db()
    logger.info("数据库初始化完成")
    
    # 检查用户配置
    users = db.get_all_users()
    if not users:
        logger.error("数据库中未找到用户配置")
        sys.exit(1)
    
    user = users[0]
    logger.info(f"使用用户: {user['email']}")
    
    # 初始化加密管理器
    from auth.crypto import CryptoManager
    crypto = CryptoManager()
    
    # 解密凭据
    try:
        password = crypto.decrypt(user['password_encrypted'])
        email = crypto.decrypt(user['email'])
    except Exception as e:
        logger.error(f"解密失败: {str(e)}")
        sys.exit(1)
    
    # API 登录
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
    
    # 更新 Token
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
    
    # 启动 WebSocket 连接（在主线程中运行）
    logger.info("正在启动 WebSocket...")
    
    # PythonAnywhere Always-on 任务有时间限制，所以不能无限循环
    # 我们运行一段时间后主动退出，让 PythonAnywhere 重新启动任务
    max_run_time = 250  # 最大运行时间（秒），小于 Always-on 任务的超时时间
    start_time = time.time()
    
    # 启动 WebSocket（使用非阻塞方式）
    import threading
    ws_thread = threading.Thread(target=ws_client.connect, daemon=False)
    ws_thread.start()
    
    # 等待 WebSocket 连接
    for i in range(10):
        if ws_client.connected:
            logger.info("✓ WebSocket 连接成功")
            break
        time.sleep(1)
    else:
        logger.warning("WebSocket 连接超时")
    
    # 启动定时任务
    from scheduler.tasks import TaskScheduler
    scheduler = TaskScheduler(ws_client, db)
    scheduler.start()
    logger.info("✓ 定时任务已启动")
    
    # 主循环（有限时间）
    logger.info(f"主循环开始，最大运行时间: {max_run_time} 秒")
    
    while running:
        # 检查运行时间
        elapsed = time.time() - start_time
        if elapsed >= max_run_time:
            logger.info(f"达到最大运行时间 {max_run_time} 秒，主动退出")
            break
        
        # 检查 WebSocket 连接状态
        if not ws_client.connected:
            logger.warning("WebSocket 连接断开，尝试重新连接...")
        
        # 短暂休眠
        time.sleep(5)
    
    # 清理并退出
    cleanup()
    logger.info("Always-on 任务正常退出")
    return 0

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n收到中断信号")
        cleanup()
        sys.exit(0)
    except Exception as e:
        logger.error(f"未捕获的异常: {str(e)}", exc_info=True)
        cleanup()
        sys.exit(1)
