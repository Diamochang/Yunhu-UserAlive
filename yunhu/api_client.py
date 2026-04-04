"""
云湖 HTTP API 客户端
处理登录、用户信息获取等 HTTP 请求
"""

import requests
import json
import time
import logging
from typing import Optional, Dict, Any

from config import Config

logger = logging.getLogger(__name__)


class YunhuAPIClient:
    """云湖 API 客户端"""
    
    def __init__(self):
        self.base_url = Config.YUNHU_API_BASE_URL
        self.session = requests.Session()
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.device_id: Optional[str] = None
        self.platform: str = "windows"
        
        # Token 管理
        self._token_refresh_interval = 3600  # Token 刷新间隔(秒)
        self._last_token_refresh: float = 0
        self._email: Optional[str] = None
        self._password: Optional[str] = None
        
        # 设置默认请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Yunhu-UserAlive/1.0'
        })
    
    def email_login(self, email: str, password: str, device_id: str, 
                    platform: str = "windows") -> Dict[str, Any]:
        """
        邮箱密码登录
        
        Args:
            email: 邮箱地址
            password: 密码
            device_id: 设备 ID
            platform: 平台标识
            
        Returns:
            包含 success、token、user_id 的字典
        """
        url = f"{self.base_url}/v1/user/email-login"
        payload = {
            "email": email,
            "password": password,
            "deviceId": device_id,
            "platform": platform
        }
        
        try:
            logger.info(f"🔐 尝试登录: {email}")
            response = self.session.post(url, json=payload, timeout=10)
            data = response.json()
            
            if data.get("code") == 1:
                self.token = data["data"]["token"]
                self.device_id = device_id
                self.platform = platform
                self._email = email
                self._password = password
                self._last_token_refresh = time.time()
                
                # 获取用户 ID
                user_info = self.get_user_info()
                if user_info and user_info.get("data"):
                    self.user_id = user_info["data"].get("id")
                
                logger.info(f"✓ 登录成功,用户 ID: {self.user_id}")
                return {
                    "success": True,
                    "token": self.token,
                    "user_id": self.user_id
                }
            else:
                error_msg = data.get("msg", "未知错误")
                logger.error(f"✗ 登录失败: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ 登录请求异常: {str(e)}")
            return {
                "success": False,
                "error": f"网络错误: {str(e)}"
            }
        except Exception as e:
            logger.error(f"✗ 登录异常: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        获取当前用户信息
        
        Returns:
            用户信息字典,失败返回 None
        """
        if not self.token:
            logger.warning("未登录,无法获取用户信息")
            return None
        
        url = f"{self.base_url}/v1/user/info"
        headers = {"token": self.token}
        
        try:
            response = self.session.get(url, headers=headers, timeout=10)
            data = response.json()
            
            if data.get("code") == 1:
                logger.debug("获取用户信息成功")
                return data
            else:
                logger.warning(f"获取用户信息失败: {data.get('msg')}")
                return None
        
        except Exception as e:
            logger.error(f"获取用户信息异常: {str(e)}")
            return None
    
    def logout(self, device_id: str = None) -> bool:
        """
        退出登录
        
        Args:
            device_id: 设备 ID
            
        Returns:
            是否成功
        """
        if not self.token:
            return True
        
        url = f"{self.base_url}/v1/user/logout"
        headers = {"token": self.token}
        payload = {
            "device-id": device_id or self.device_id
        }
        
        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=10)
            data = response.json()
            
            if data.get("code") == 1:
                logger.info("退出登录成功")
                self.token = None
                self.user_id = None
                return True
            else:
                logger.warning(f"退出登录失败: {data.get('msg')}")
                return False
        
        except Exception as e:
            logger.error(f"退出登录异常: {str(e)}")
            return False
    
    def check_token_valid(self) -> bool:
        """
        检查 Token 是否有效
        
        Returns:
            Token 是否有效
        """
        user_info = self.get_user_info()
        return user_info is not None and user_info.get("code") == 1
    
    def refresh_token_if_needed(self) -> bool:
        """
        检查并刷新 Token(如果需要)
        
        Returns:
            是否成功刷新或Token仍然有效
        """
        import time
        
        # 检查是否需要刷新
        elapsed = time.time() - self._last_token_refresh
        if elapsed < self._token_refresh_interval:
            return True
        
        # 检查凭证是否存在
        if not self._email or not self._password:
            logger.warning("⚠️ 缺少登录凭证,无法刷新Token")
            return self.check_token_valid()
        
        logger.info(f"🔄 Token 已使用 {elapsed:.0f} 秒,尝试刷新...")
        
        # 重试机制:最多重试3次
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"尝试重新登录 ({attempt}/{max_retries})...")
                result = self.email_login(
                    email=self._email,
                    password=self._password,
                    device_id=self.device_id,
                    platform=self.platform
                )
                
                if result["success"]:
                    logger.info("✓ Token 刷新成功")
                    return True
                else:
                    logger.warning(f"✗ 第{attempt}次尝试失败: {result.get('error')}")
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # 指数退避: 2s, 4s
            except Exception as e:
                logger.error(f"✗ 第{attempt}次尝试异常: {str(e)}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
        
        logger.error(f"✗ Token 刷新失败,已重试 {max_retries} 次")
        return False
    
    def set_credentials(self, email: str, password: str):
        """设置登录凭证(用于Token刷新)"""
        self._email = email
        self._password = password
        logger.debug("登录凭证已设置")
    
    @property
    def token_age(self) -> float:
        """获取Token已使用时间(秒)"""
        import time
        if self._last_token_refresh == 0:
            return 0
        return time.time() - self._last_token_refresh
