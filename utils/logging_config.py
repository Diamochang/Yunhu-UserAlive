"""
增强的日志系统配置
支持结构化日志、文件轮转、多级别日志
"""
import logging
import sys
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime


class LogFormatter(logging.Formatter):
    """自定义日志格式化器,支持彩色输出"""
    
    # ANSI 颜色代码
    COLORS = {
        'DEBUG': '\033[36m',     # 青色
        'INFO': '\033[32m',      # 绿色
        'WARNING': '\033[33m',   # 黄色
        'ERROR': '\033[31m',     # 红色
        'CRITICAL': '\033[1;31m' # 亮红色
    }
    RESET = '\033[0m'
    
    def __init__(self, use_color=True):
        super().__init__()
        self.use_color = use_color
        self.default_format = (
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
        )
        self.detailed_format = (
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
        )
    
    def format(self, record):
        # 保存原始状态
        orig_levelname = record.levelname
        
        # 添加颜色
        if self.use_color and record.levelname in self.COLORS:
            color = self.COLORS[record.levelname]
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        # 根据日志级别选择格式
        if record.levelno >= logging.ERROR:
            formatter = logging.Formatter(self.detailed_format)
        else:
            formatter = logging.Formatter(self.default_format)
        
        result = formatter.format(record)
        
        # 恢复原始状态
        record.levelname = orig_levelname
        return result


def setup_logging(log_file='logs/app.log', 
                  log_level=logging.INFO,
                  max_bytes=10*1024*1024,  # 10MB
                  backup_count=5,
                  console_output=True):
    """
    配置日志系统
    
    Args:
        log_file: 日志文件路径
        log_level: 日志级别
        max_bytes: 单个日志文件最大大小
        backup_count: 保留的备份文件数量
        console_output: 是否输出到控制台
    """
    # 确保日志目录存在
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    # 获取根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除已有的处理器(避免重复添加)
    root_logger.handlers.clear()
    
    # 控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = LogFormatter(use_color=True)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # 文件处理器 - 按大小轮转
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = LogFormatter(use_color=False)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 错误日志单独文件
    error_log_file = log_file.replace('.log', '_error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # 减少第三方库的日志输出
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('websocket').setLevel(logging.WARNING)
    logging.getLogger('flask').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)
    
    # 记录启动信息
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("日志系统初始化完成")
    logger.info(f"日志级别: {logging.getLevelName(log_level)}")
    logger.info(f"日志文件: {log_file}")
    logger.info(f"错误日志: {error_log_file}")
    logger.info("=" * 60)
    
    return root_logger


def get_logger(name=None):
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称(通常为 __name__)
        
    Returns:
        Logger 实例
    """
    return logging.getLogger(name)


# 异常处理装饰器
def handle_exceptions(logger_name=None):
    """
    异常处理装饰器,自动捕获并记录异常
    
    Args:
        logger_name: 日志记录器名称
        
    Usage:
        @handle_exceptions('my_module')
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or func.__module__)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"函数 {func.__name__} 执行失败: {str(e)}",
                    exc_info=True,
                    extra={
                        'function': func.__name__,
                        'module': func.__module__,
                        'error_type': type(e).__name__
                    }
                )
                raise
        return wrapper
    return decorator
