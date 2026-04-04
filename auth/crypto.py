"""
加密模块
使用 Fernet 对称加密 + PBKDF2 密钥派生
bcrypt 用于密码哈希(生产环境推荐)
"""

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
import base64
import os
import logging

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    logging.warning("⚠️ bcrypt未安装,将使用PBKDF2作为后备方案")

from config import Config

logger = logging.getLogger(__name__)


class CryptoManager:
    """加密管理器,使用单例模式"""
    
    _instance = None
    _fernet = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._init_crypto()
        return cls._instance
    
    @classmethod
    def _init_crypto(cls):
        """初始化加密组件"""
        master_password = Config.MASTER_PASSWORD
        salt = Config.ENCRYPTION_SALT.encode()
        
        if not master_password:
            raise ValueError("MASTER_PASSWORD 未配置")
        
        # 使用 PBKDF2 从主密码派生密钥
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,  # OWASP 推荐的最小迭代次数
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        cls._fernet = Fernet(key)
        logger.info("加密模块初始化完成")
    
    def encrypt(self, data: str) -> bytes:
        """
        加密字符串数据
        
        Args:
            data: 要加密的明文
            
        Returns:
            加密后的字节数据(Base64 编码)
        """
        try:
            encrypted = self._fernet.encrypt(data.encode('utf-8'))
            return base64.b64encode(encrypted)
        except Exception as e:
            logger.error(f"加密失败: {str(e)}")
            raise
    
    def decrypt(self, encrypted_data: bytes) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密的字节数据(Base64 编码)
            
        Returns:
            解密后的明文字符串
        """
        try:
            # 如果是 Base64 编码的,先解码
            if isinstance(encrypted_data, str):
                encrypted_data = base64.b64decode(encrypted_data)
            elif isinstance(encrypted_data, bytes):
                # 检查是否已经是 Base64 编码
                try:
                    encrypted_data = base64.b64decode(encrypted_data)
                except Exception:
                    pass  # 不是 Base64,直接使用
            
            decrypted = self._fernet.decrypt(encrypted_data)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"解密失败: {str(e)}")
            raise
    
    @staticmethod
    def generate_salt() -> str:
        """生成随机盐值"""
        return base64.b64encode(os.urandom(32)).decode('utf-8')
    
    @staticmethod
    def hash_password(password: str) -> bytes:
        """
        对密码进行哈希处理(用于 Web 登录验证)
        优先使用 bcrypt,如果不可用则回退到 PBKDF2
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码(bcrypt返回bytes, PBKDF2返回base64编码的bytes)
        """
        if HAS_BCRYPT:
            # 使用 bcrypt (推荐)
            salt = bcrypt.gensalt(rounds=12)  # 12轮迭代,平衡安全性和性能
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            logger.debug("使用 bcrypt 哈希密码")
            return hashed
        else:
            # 回退到 PBKDF2
            logger.warning("⚠️ 使用 PBKDF2 哈希密码(建议安装 bcrypt)")
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            import base64
            
            salt = Config.ENCRYPTION_SALT.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return base64.b64encode(kdf.derive(password.encode('utf-8')))
    
    @staticmethod
    def verify_password(password: str, hashed_password: bytes) -> bool:
        """
        验证密码
        
        Args:
            password: 明文密码
            hashed_password: 哈希后的密码
            
        Returns:
            密码是否匹配
        """
        if HAS_BCRYPT and not hashed_password.startswith(b'base64:'):
            # 使用 bcrypt 验证
            try:
                result = bcrypt.checkpw(password.encode('utf-8'), hashed_password)
                logger.debug("使用 bcrypt 验证密码")
                return result
            except Exception as e:
                logger.error(f"bcrypt 验证失败: {str(e)}")
                return False
        else:
            # 回退到 PBKDF2 验证(兼容旧数据)
            logger.warning("⚠️ 使用 PBKDF2 验证密码(建议迁移到 bcrypt)")
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes
            import base64
            
            # 检查是否是base64编码的PBKDF2哈希
            if hashed_password.startswith(b'base64:'):
                stored_hash = base64.b64decode(hashed_password[7:])
            else:
                stored_hash = hashed_password
            
            salt = Config.ENCRYPTION_SALT.encode()
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            computed_hash = base64.b64encode(kdf.derive(password.encode('utf-8')))
            return computed_hash == stored_hash
