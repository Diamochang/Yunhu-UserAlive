"""
云湖 WebSocket 客户端
处理 WebSocket 连接、消息收发、心跳保活
"""

import websocket
import json
import uuid
import time
import threading
import logging
from typing import Optional, Callable, Dict, Any

from config import Config
from proto.serializer import serializer

logger = logging.getLogger(__name__)

# 允许的平台列表(大小写敏感)
ALLOWED_PLATFORMS = ["windows", "macos", "android", "linux", "ios", "fuchsia", "Web"]


class YunhuWebSocketClient:
    """云湖 WebSocket 客户端"""
    
    def __init__(self, user_id: str, token: str, device_id: str, platform: str = "windows"):
        # 验证平台名称
        if platform not in ALLOWED_PLATFORMS:
            logger.warning(f"⚠️ 平台名称 '{platform}' 不在允许列表中,将使用 'windows'")
            logger.warning(f"允许的平台: {', '.join(ALLOWED_PLATFORMS)}")
            platform = "windows"
        
        self.user_id = user_id
        self.token = token
        self.device_id = device_id
        self.platform = platform
        self.ws_url = Config.YUNHU_WS_URL
        
        self.ws: Optional[websocket.WebSocketApp] = None
        self.message_callback: Optional[Callable] = None
        self.connected = False
        self._reconnect_delay = 5  # 初始重连延迟(秒)
        self._max_reconnect_delay = 300  # 最大重连延迟(秒)
        self._running = False
        
        # 心跳相关
        self._heartbeat_interval = 30  # 心跳间隔(秒)
        self._heartbeat_timer: Optional[threading.Timer] = None
        self._last_pong_time: float = 0
        
        # 统计信息
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "reconnections": 0,
            "last_connect_time": None,
            "uptime_seconds": 0
        }
    
    def connect(self):
        """建立 WebSocket 连接并登录"""
        self._running = True
        reconnect_count = 0
        max_reconnect_attempts = 50  # 最大重连次数
        
        while self._running:
            try:
                logger.info(f"正在连接 WebSocket: {self.ws_url} (尝试 #{reconnect_count + 1})")
                
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close,
                    on_open=self._on_open
                )
                
                # 设置连接选项
                self.ws.run_forever(
                    ping_interval=60,  # 每60秒发送ping
                    ping_timeout=10,   # ping超时10秒
                    ping_payload="ping"  # ping载荷
                )
                
            except Exception as e:
                logger.error(f"WebSocket 连接异常: {str(e)}", exc_info=True)
            
            if self._running:
                reconnect_count += 1
                self.stats["reconnections"] = reconnect_count
                
                # 检查是否超过最大重连次数
                if reconnect_count >= max_reconnect_attempts:
                    logger.error(f"✗ 达到最大重连次数 ({max_reconnect_attempts}),停止重连")
                    self._running = False
                    break
                
                # 指数退避重连
                logger.info(f"{self._reconnect_delay} 秒后尝试重连... (已重连 {reconnect_count} 次)")
                time.sleep(self._reconnect_delay)
                self._reconnect_delay = min(
                    self._reconnect_delay * 2,
                    self._max_reconnect_delay
                )
    
    def disconnect(self):
        """断开 WebSocket 连接"""
        self._running = False
        if self.ws:
            self.ws.close()
        self.connected = False
        logger.info("WebSocket 已断开")
    
    def _on_open(self, ws):
        """连接成功后发送登录指令"""
        logger.info("✓ WebSocket 连接成功,发送登录指令")
        
        # 使用ProtoBuf或JSON序列化登录消息
        login_data = serializer.serialize_login(
            user_id=self.user_id,
            token=self.token,
            platform=self.platform,
            device_id=self.device_id
        )
        
        ws.send(login_data)
        self.connected = True
        self._reconnect_delay = 5  # 重置重连延迟
        self._last_pong_time = time.time()
        self.stats["last_connect_time"] = time.time()
        
        logger.info(f"✓ 登录指令已发送 (用户: {self.user_id}, 平台: {self.platform})")
        
        # 启动心跳定时器
        self._start_heartbeat()
    
    def _on_message(self, ws, message):
        """接收消息"""
        try:
            self.stats["messages_received"] += 1
            
            # 尝试解析消息
            data = serializer.deserialize_message(message)
            
            if data is None:
                logger.warning(f"收到无法解析的消息")
                return
            
            cmd = data.get('cmd', data.get('info', {}).get('cmd', 'unknown'))
            logger.debug(f"收到消息: {cmd}")
            
            # 处理心跳响应
            if cmd == 'heartbeat_ack':
                self._last_pong_time = time.time()
                logger.debug("✓ 心跳响应正常")
                return
            
            # 调用消息回调
            if self.message_callback:
                self.message_callback(data)
        
        except Exception as e:
            logger.error(f"处理消息异常: {str(e)}", exc_info=True)
    
    def _on_error(self, ws, error):
        """错误处理"""
        error_str = str(error)
        
        # 分类错误类型
        if "Connection refused" in error_str or "Connection reset" in error_str:
            logger.error(f"✗ WebSocket 连接被拒绝或重置: {error_str}")
        elif "timed out" in error_str.lower():
            logger.warning(f"⚠️ WebSocket 连接超时: {error_str}")
        elif "SSL" in error_str or "certificate" in error_str.lower():
            logger.error(f"✗ SSL/TLS 错误: {error_str}")
        else:
            logger.error(f"✗ WebSocket 错误: {error_str}")
        
        self.connected = False
        # 停止心跳
        self._stop_heartbeat()
    
    def _on_close(self, ws, close_status_code, close_msg):
        """连接关闭"""
        close_msg_str = close_msg.decode('utf-8') if isinstance(close_msg, bytes) else str(close_msg)
        
        # 根据关闭码判断原因
        if close_status_code == 1000:
            logger.info("✓ WebSocket 正常关闭")
        elif close_status_code == 1001:
            logger.warning("⚠️ WebSocket 连接断开(服务端离开)")
        elif close_status_code == 1006:
            logger.error("✗ WebSocket 异常断开(未收到关闭帧)")
        elif close_status_code == 1008:
            logger.error("✗ WebSocket 策略违规(可能是Token过期)")
        elif close_status_code == 1009:
            logger.error("✗ WebSocket 消息过大")
        else:
            logger.info(f"WebSocket 连接关闭: code={close_status_code}, msg={close_msg_str}")
        
        self.connected = False
        # 停止心跳
        self._stop_heartbeat()
    
    def send_message(self, chat_id: str, chat_type: int, text: str, 
                     content_type: int = 1, quote_msg_id: str = None) -> bool:
        """
        发送消息
        
        Args:
            chat_id: 聊天对象 ID(用户/群聊/机器人)
            chat_type: 聊天类型 (1-用户, 2-群聊, 3-机器人)
            text: 消息文本
            content_type: 内容类型 (1-文本, 3-Markdown, 8-HTML)
            quote_msg_id: 引用消息 ID(可选)
            
        Returns:
            是否发送成功
        """
        if not self.connected or not self.ws:
            logger.warning("⚠️ WebSocket 未连接,无法发送消息")
            return False
        
        try:
            # 使用ProtoBuf或JSON序列化消息
            msg_data = serializer.serialize_send_message(
                chat_id=chat_id,
                chat_type=chat_type,
                text=text,
                content_type=content_type,
                quote_msg_id=quote_msg_id
            )
            
            # 构造WebSocket消息框架
            ws_message = {
                "seq": str(uuid.uuid4().hex),
                "cmd": "sendMsg",
                "data": json.loads(msg_data.decode('utf-8')) if isinstance(msg_data, bytes) else msg_data
            }
            
            self.ws.send(json.dumps(ws_message))
            self.stats["messages_sent"] += 1
            logger.debug(f"✓ 消息已发送到 {chat_id} (类型: {chat_type})")
            return True
        
        except Exception as e:
            logger.error(f"✗ 发送消息失败: {str(e)}", exc_info=True)
            return False
    
    def send_text_message(self, chat_id: str, chat_type: int, text: str) -> bool:
        """发送文本消息(快捷方法)"""
        return self.send_message(chat_id, chat_type, text, content_type=1)
    
    def send_markdown_message(self, chat_id: str, chat_type: int, markdown: str) -> bool:
        """发送 Markdown 消息(快捷方法)"""
        return self.send_message(chat_id, chat_type, markdown, content_type=3)
    
    def _start_heartbeat(self):
        """启动心跳定时器"""
        self._stop_heartbeat()  # 先停止已有的定时器
        self._heartbeat_timer = threading.Timer(
            self._heartbeat_interval, 
            self._send_heartbeat
        )
        self._heartbeat_timer.daemon = True
        self._heartbeat_timer.start()
        logger.debug(f"心跳定时器已启动 (间隔: {self._heartbeat_interval}秒)")
    
    def _stop_heartbeat(self):
        """停止心跳定时器"""
        if self._heartbeat_timer:
            self._heartbeat_timer.cancel()
            self._heartbeat_timer = None
            logger.debug("心跳定时器已停止")
    
    def _send_heartbeat(self):
        """发送心跳包"""
        if not self.connected or not self.ws:
            logger.debug("WebSocket 未连接,跳过心跳")
            return
        
        try:
            # 检查上次心跳响应时间
            elapsed = time.time() - self._last_pong_time
            if elapsed > self._heartbeat_interval * 2:
                logger.warning(f"⚠️ 心跳超时 ({elapsed:.1f}秒),可能连接已断开")
                self.connected = False
                if self.ws:
                    self.ws.close()
                return
            
            # 发送心跳
            heartbeat_data = serializer.serialize_heartbeat()
            self.ws.send(heartbeat_data)
            logger.debug("♥ 心跳已发送")
            
            # 重启定时器
            self._start_heartbeat()
            
        except Exception as e:
            logger.error(f"✗ 发送心跳失败: {str(e)}")
            self.connected = False
    
    def get_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        stats = self.stats.copy()
        if stats["last_connect_time"]:
            stats["uptime_seconds"] = time.time() - stats["last_connect_time"]
        
        # 添加 ProtoBuf 状态
        from proto.serializer import serializer
        stats["proto_support"] = serializer.is_proto_available
        stats["proto_status"] = serializer.get_status_report()
        stats["platform"] = self.platform
        return stats
    
    def update_token(self, new_token: str):
        """更新Token(用于Token刷新)"""
        old_token = self.token[:10] + "..." if len(self.token) > 10 else self.token
        self.token = new_token
        logger.info(f"✓ Token已更新 (旧: {old_token})")
