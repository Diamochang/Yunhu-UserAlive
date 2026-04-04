"""
TOTP (基于时间的一次性密码) 模块
用于双因素认证 (2FA)
"""

import pyotp
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class TOTPManager:
    """TOTP 管理器"""
    
    @staticmethod
    def generate_secret() -> str:
        """
        生成 TOTP 密钥
        
        Returns:
            Base32 编码的密钥字符串
        """
        secret = pyotp.random_base32()
        logger.info("生成新的 TOTP 密钥")
        return secret
    
    @staticmethod
    def get_provisioning_uri(secret: str, username: str, issuer_name: str = "Yunhu-UserAlive") -> str:
        """
        获取 TOTP 配置 URI(用于生成 QR 码)
        
        Args:
            secret: TOTP 密钥
            username: 用户名(通常是邮箱)
            issuer_name: 发行者名称
            
        Returns:
            otpauth:// URI
        """
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=username, issuer_name=issuer_name)
        return uri
    
    @staticmethod
    def verify_code(secret: str, code: str, valid_window: int = 1) -> bool:
        """
        验证 TOTP 验证码
        
        Args:
            secret: TOTP 密钥
            code: 用户输入的 6 位验证码
            valid_window: 允许的时间窗口(前后各多少个周期)
            
        Returns:
            验证是否成功
        """
        try:
            totp = pyotp.TOTP(secret)
            is_valid = totp.verify(code, valid_window=valid_window)
            
            if is_valid:
                logger.debug("TOTP 验证码验证成功")
            else:
                logger.warning("TOTP 验证码验证失败")
            
            return is_valid
        except Exception as e:
            logger.error(f"TOTP 验证异常: {str(e)}")
            return False
    
    @staticmethod
    def get_current_code(secret: str) -> str:
        """
        获取当前的 TOTP 验证码(用于测试)
        
        Args:
            secret: TOTP 密钥
            
        Returns:
            6 位验证码
        """
        totp = pyotp.TOTP(secret)
        return totp.now()
    
    @staticmethod
    def generate_qr_code_image(uri: str, filename: str = "totp_qr.png"):
        """
        生成 TOTP QR 码图片
        
        Args:
            uri: otpauth:// URI
            filename: 输出文件名
        """
        try:
            import qrcode
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(filename)
            logger.info(f"TOTP QR 码已保存到: {filename}")
        except ImportError:
            logger.warning("qrcode 库未安装,无法生成 QR 码图片")
            raise ImportError("请安装 qrcode: pip install qrcode[pil]")
