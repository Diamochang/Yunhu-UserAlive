"""
数据库管理器
提供所有数据库操作的封装
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from config import Config
from database.models import CREATE_TABLES_SQL

logger = logging.getLogger(__name__)


class DatabaseManager:
    """数据库管理器单例"""
    
    _instance = None
    _db_path = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._db_path = Config.DATABASE_PATH
            # 初始化查询缓存
            cls._query_cache = {}
            cls._cache_ttl = 60  # 缓存有效期(秒)
        return cls._instance
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
        # 启用WAL模式以提高并发性能
        conn.execute("PRAGMA journal_mode=WAL")
        # 启用外键约束
        conn.execute("PRAGMA foreign_keys=ON")
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            conn.close()
    
    def init_db(self):
        """初始化数据库,创建所有表"""
        with self.get_connection() as conn:
            conn.executescript(CREATE_TABLES_SQL)
            logger.info("数据库初始化完成")
    
    # ==================== 用户管理 ====================
    
    def add_user(self, email: str, password_encrypted: bytes, device_id: str, 
                 platform: str = 'windows') -> int:
        """添加新用户"""
        with self.get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (email, password_encrypted, device_id, platform) VALUES (?, ?, ?, ?)",
                (email, password_encrypted, device_id, platform)
            )
            user_id = cursor.lastrowid
            
            # 为该用户创建默认设置
            conn.execute(
                "INSERT INTO settings (user_id) VALUES (?)",
                (user_id,)
            )
            
            logger.info(f"添加新用户: {email}, ID: {user_id}")
            return user_id
    
    def get_user_by_id(self, user_id: int) -> Optional[sqlite3.Row]:
        """根据 ID 获取用户"""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    def get_user_by_email(self, email: str) -> Optional[sqlite3.Row]:
        """根据邮箱获取用户"""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    
    def get_user_by_yunhu_id(self, yunhu_user_id: str) -> Optional[sqlite3.Row]:
        """根据云湖用户ID获取本地用户"""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM users WHERE user_id = ?", (yunhu_user_id,)).fetchone()
    
    def get_all_users(self) -> List[sqlite3.Row]:
        """获取所有用户"""
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM users").fetchall()
    
    def get_user_count(self) -> int:
        """获取用户总数"""
        with self.get_connection() as conn:
            result = conn.execute("SELECT COUNT(*) as count FROM users").fetchone()
            return result['count'] if result else 0
    
    def update_user_token(self, user_id: int, token: str, yunhu_user_id: str):
        """更新用户 Token 和云湖用户 ID"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE users SET token = ?, user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (token, yunhu_user_id, user_id)
            )
    
    def authenticate_user(self, email: str, password_plain: str) -> Optional[sqlite3.Row]:
        """
        验证用户(用于 Web 登录)
        
        Args:
            email: 邮箱
            password_plain: 明文密码
            
        Returns:
            用户信息,验证失败返回None
        """
        with self.get_connection() as conn:
            user = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            ).fetchone()
            
            if not user:
                return None
            
            # 使用 CryptoManager 验证密码
            from auth.crypto import CryptoManager
            crypto = CryptoManager()
            
            try:
                # 验证密码(传入明文密码和存储的哈希值)
                stored_hash = user['password_encrypted']
                if crypto.verify_password(password_plain, stored_hash):
                    return user
            except Exception as e:
                logger.error(f"密码验证异常: {str(e)}")
            
            return None
    
    # ==================== 用户设置管理 ====================
    
    def get_user_settings(self, user_id: int) -> Optional[sqlite3.Row]:
        """获取用户设置(带缓存)"""
        cache_key = f"settings_{user_id}"
        
        # 检查缓存
        if cache_key in self._query_cache:
            cached_data, timestamp = self._query_cache[cache_key]
            import time
            if time.time() - timestamp < self._cache_ttl:
                logger.debug(f"使用缓存的用户设置: user_id={user_id}")
                return cached_data
        
        # 从数据库查询
        with self.get_connection() as conn:
            result = conn.execute(
                "SELECT * FROM settings WHERE user_id = ?",
                (user_id,)
            ).fetchone()
            
            # 更新缓存
            if result:
                import time
                self._query_cache[cache_key] = (result, time.time())
            
            return result
    
    def update_takeover_settings(self, user_id: int, enabled: bool, 
                                 start_time: str, end_time: str):
        """更新自动接管设置"""
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE settings 
                   SET auto_takeover_enabled = ?, 
                       takeover_start_time = ?, 
                       takeover_end_time = ?,
                       updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?""",
                (enabled, start_time, end_time, user_id)
            )
        # 清除缓存
        self._clear_cache(f"settings_{user_id}")
    
    def update_last_console_access(self, user_id: int):
        """更新最后访问控制台时间"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE settings SET last_console_access = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (user_id,)
            )
    
    def set_auto_final_farewell_delay(self, user_id: int, delay_seconds: int):
        """设置自动开启电子终别延迟"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE settings SET auto_final_farewell_delay = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (delay_seconds, user_id)
            )
        # 清除缓存
        self._clear_cache(f"settings_{user_id}")
    
    def set_global_final_farewell(self, user_id: int, enabled: bool):
        """设置全局电子终别标记"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE settings SET global_final_farewell = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (enabled, user_id)
            )
        # 清除缓存
        self._clear_cache(f"settings_{user_id}")
    
    def get_global_final_farewell(self, user_id: int) -> bool:
        """获取全局电子终别标记状态"""
        settings = self.get_user_settings(user_id)
        return settings['global_final_farewell'] if settings else False
    
    def set_auto_takeover(self, user_id: int, enabled: bool):
        """设置自动接管开关"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE settings SET auto_takeover_enabled = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (enabled, user_id)
            )
        # 清除缓存
        self._clear_cache(f"settings_{user_id}")
    
    def _clear_cache(self, key: str = None):
        """
        清除查询缓存
        
        Args:
            key: 指定要清除的缓存键,如果为None则清除所有缓存
        """
        if key:
            if key in self._query_cache:
                del self._query_cache[key]
                logger.debug(f"清除缓存: {key}")
        else:
            cache_size = len(self._query_cache)
            self._query_cache.clear()
            logger.debug(f"清除所有缓存 ({cache_size}个条目)")
    
    def get_all_users_with_settings(self) -> List[Dict[str, Any]]:
        """获取所有用户及其设置(用于定时任务检查)"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT u.id, u.email, s.auto_final_farewell_delay, s.last_console_access
                FROM users u
                JOIN settings s ON u.id = s.user_id
            """).fetchall()
            
            result = []
            for row in rows:
                result.append({
                    'id': row['id'],
                    'email': row['email'],
                    'auto_final_farewell_delay': row['auto_final_farewell_delay'],
                    'last_console_access': row['last_console_access']
                })
            return result
    
    # ==================== 文章链接管理 ====================
    
    def add_article_link(self, user_id: int, title: str, url: str):
        """添加文章链接"""
        settings = self.get_user_settings(user_id)
        if not settings:
            raise ValueError(f"用户 {user_id} 的设置不存在")
        
        # 获取现有文章列表
        article_links = json.loads(settings['article_links']) if settings['article_links'] else []
        
        # 添加新文章
        article_links.append({'title': title, 'url': url})
        
        # 保存回数据库
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE settings SET article_links = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (json.dumps(article_links), user_id)
            )
    
    def remove_article_link(self, user_id: int, index: int):
        """删除文章链接(按索引)"""
        settings = self.get_user_settings(user_id)
        if not settings or not settings['article_links']:
            return
        
        article_links = json.loads(settings['article_links'])
        if 0 <= index < len(article_links):
            article_links.pop(index)
            
            with self.get_connection() as conn:
                conn.execute(
                    "UPDATE settings SET article_links = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (json.dumps(article_links), user_id)
                )
    
    def get_article_links(self, user_id: int) -> List[Dict[str, str]]:
        """获取用户的文章链接列表"""
        settings = self.get_user_settings(user_id)
        if settings and settings['article_links']:
            return json.loads(settings['article_links'])
        return []
    
    # ==================== 好友管理 ====================
    
    def add_friend(self, user_id: int, friend_chat_id: str, friend_name: str,
                   encrypted_address: str = None, local_final_farewell: bool = False):
        """添加信任好友"""
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO friends 
                   (user_id, friend_chat_id, friend_name, encrypted_address, local_final_farewell)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, friend_chat_id, friend_name, encrypted_address, local_final_farewell)
            )
    
    def remove_friend(self, user_id: int, friend_chat_id: str):
        """删除信任好友"""
        with self.get_connection() as conn:
            conn.execute(
                "DELETE FROM friends WHERE user_id = ? AND friend_chat_id = ?",
                (user_id, friend_chat_id)
            )
    
    def get_friends(self, user_id: int) -> List[sqlite3.Row]:
        """获取用户的所有信任好友"""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM friends WHERE user_id = ?",
                (user_id,)
            ).fetchall()
    
    def get_friend_by_chat_id(self, user_id: int, friend_chat_id: str) -> Optional[sqlite3.Row]:
        """根据云湖 ID 获取好友"""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM friends WHERE user_id = ? AND friend_chat_id = ?",
                (user_id, friend_chat_id)
            ).fetchone()
    
    def update_friend_address(self, user_id: int, friend_chat_id: str, encrypted_address: str):
        """更新好友的加密住址"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE friends SET encrypted_address = ? WHERE user_id = ? AND friend_chat_id = ?",
                (encrypted_address, user_id, friend_chat_id)
            )
    
    def toggle_local_final_farewell(self, user_id: int, friend_chat_id: str):
        """切换局部电子终别标记"""
        with self.get_connection() as conn:
            conn.execute(
                """UPDATE friends 
                   SET local_final_farewell = NOT local_final_farewell 
                   WHERE user_id = ? AND friend_chat_id = ?""",
                (user_id, friend_chat_id)
            )
    
    # ==================== TOTP 管理 ====================
    
    def set_totp_secret(self, user_id: int, secret_key: str):
        """设置用户的 TOTP 密钥"""
        with self.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO totp_secrets (user_id, secret_key, is_active)
                   VALUES (?, ?, 1)""",
                (user_id, secret_key)
            )
    
    def get_totp_secret(self, user_id: int) -> Optional[sqlite3.Row]:
        """获取用户的 TOTP 密钥"""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM totp_secrets WHERE user_id = ? AND is_active = 1",
                (user_id,)
            ).fetchone()
    
    def disable_totp(self, user_id: int):
        """禁用用户的 TOTP"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE totp_secrets SET is_active = 0 WHERE user_id = ?",
                (user_id,)
            )
    
    # ==================== 签到记录 ====================
    
    def record_checkin(self, user_id: int, success: bool, error_message: str = None):
        """记录签到结果"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT INTO checkin_records (user_id, success, error_message) VALUES (?, ?, ?)",
                (user_id, success, error_message)
            )
    
    def get_last_checkin(self, user_id: int) -> Optional[sqlite3.Row]:
        """获取最后一次签到记录"""
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM checkin_records WHERE user_id = ? ORDER BY checkin_time DESC LIMIT 1",
                (user_id,)
            ).fetchone()
    
    # ==================== 辅助方法 ====================
    
    def verify_password(self, user_id: int, password_encrypted: bytes) -> bool:
        """验证密码(用于敏感操作)"""
        user = self.get_user_by_id(user_id)
        if user:
            return user['password_encrypted'] == password_encrypted
        return False
