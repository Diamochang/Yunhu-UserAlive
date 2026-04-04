"""
ProtoBuf消息序列化工具
用于云湖WebSocket消息的序列化和反序列化
"""
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ProtoBufSerializer:
    """ProtoBuf消息序列化器(简化版,使用JSON作为后备)"""
    
    def __init__(self):
        self._use_proto = False
        try:
            # 尝试导入编译后的proto文件
            from proto.generated import yunhu_pb2
            self.yunhu_pb2 = yunhu_pb2
            self._use_proto = True
            logger.info("✓ ProtoBuf支持已启用")
        except ImportError as e:
            logger.warning(f"⚠ ProtoBuf模块未找到,将使用JSON格式: {e}")
            logger.warning("如需启用ProtoBuf,请运行: bash proto/compile.sh")
    
    def serialize_login(self, user_id: str, token: str, platform: str, 
                       device_id: str, seq: str = None) -> bytes:
        """
        序列化WebSocket登录消息
        
        Args:
            user_id: 用户ID
            token: 登录令牌
            platform: 平台名称(windows/macos/android/linux/ios/fuchsia/Web)
            device_id: 设备ID
            seq: 请求序列号
            
        Returns:
            序列化后的消息(bytes或str)
        """
        import uuid
        if seq is None:
            seq = uuid.uuid4().hex
        
        message = {
            "seq": seq,
            "cmd": "login",
            "data": {
                "userId": user_id,
                "token": token,
                "platform": platform,
                "deviceId": device_id
            }
        }
        
        if self._use_proto:
            try:
                login_msg = self.yunhu_pb2.WSLogin()
                login_msg.seq = seq
                login_msg.cmd = "login"
                login_msg.data.userId = user_id
                login_msg.data.token = token
                login_msg.data.platform = platform
                login_msg.data.deviceId = device_id
                return login_msg.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def serialize_heartbeat(self, seq: str = None) -> bytes:
        """
        序列化心跳消息
        
        Args:
            seq: 请求序列号
            
        Returns:
            序列化后的消息
        """
        import uuid
        if seq is None:
            seq = uuid.uuid4().hex
        
        message = {
            "seq": seq,
            "cmd": "heartbeat",
            "data": {}
        }
        
        if self._use_proto:
            try:
                heartbeat_msg = self.yunhu_pb2.WSHeartbeat()
                heartbeat_msg.seq = seq
                heartbeat_msg.cmd = "heartbeat"
                return heartbeat_msg.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def serialize_send_message(self, chat_id: str, chat_type: int, 
                              text: str, content_type: int = 1,
                              msg_id: str = None, quote_msg_id: str = None) -> bytes:
        """
        序列化发送消息请求
        
        Args:
            chat_id: 聊天对象ID
            chat_type: 聊天类型(1-用户, 2-群聊, 3-机器人)
            text: 消息文本
            content_type: 内容类型(1-文本, 3-Markdown, 8-HTML)
            msg_id: 消息ID(可选)
            quote_msg_id: 引用消息ID(可选)
            
        Returns:
            序列化后的消息
        """
        import uuid
        if msg_id is None:
            msg_id = uuid.uuid4().hex
        
        message = {
            "msg_id": msg_id,
            "chat_id": chat_id,
            "chat_type": chat_type,
            "data": {
                "text": text
            },
            "content_type": content_type
        }
        
        if quote_msg_id:
            message["quote_msg_id"] = quote_msg_id
        
        if self._use_proto:
            try:
                send_msg = self.yunhu_pb2.SendMessageRequest()
                send_msg.msg_id = msg_id
                send_msg.chat_id = chat_id
                send_msg.chat_type = chat_type
                send_msg.data.text = text
                send_msg.content_type = content_type
                if quote_msg_id:
                    send_msg.quote_msg_id = quote_msg_id
                return send_msg.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def serialize_read_message(self, chat_id: str, chat_type: int, 
                               last_msg_id: str = None) -> bytes:
        """
        序列化已读消息请求
        
        Args:
            chat_id: 聊天对象ID
            chat_type: 聊天类型
            last_msg_id: 最后一条消息ID
            
        Returns:
            序列化后的消息
        """
        import uuid
        seq = uuid.uuid4().hex
        
        message = {
            "seq": seq,
            "cmd": "readMsg",
            "data": {
                "chatId": chat_id,
                "chatType": chat_type,
                "lastMsgId": last_msg_id or ""
            }
        }
        
        if self._use_proto:
            try:
                read_msg = self.yunhu_pb2.ReadMessageRequest()
                read_msg.seq = seq
                read_msg.cmd = "readMsg"
                read_msg.data.chatId = chat_id
                read_msg.data.chatType = chat_type
                read_msg.data.lastMsgId = last_msg_id or ""
                return read_msg.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def serialize_get_chat_list(self, page: int = 1, page_size: int = 20) -> bytes:
        """
        序列化获取聊天列表请求
        
        Args:
            page: 页码
            page_size: 每页数量
            
        Returns:
            序列化后的消息
        """
        import uuid
        seq = uuid.uuid4().hex
        
        message = {
            "seq": seq,
            "cmd": "getChatList",
            "data": {
                "page": page,
                "pageSize": page_size
            }
        }
        
        if self._use_proto:
            try:
                chat_list_req = self.yunhu_pb2.GetChatListRequest()
                chat_list_req.seq = seq
                chat_list_req.cmd = "getChatList"
                chat_list_req.data.page = page
                chat_list_req.data.pageSize = page_size
                return chat_list_req.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def serialize_logout(self, device_id: str) -> bytes:
        """
        序列化退出登录请求
        
        Args:
            device_id: 设备ID
            
        Returns:
            序列化后的消息
        """
        import uuid
        seq = uuid.uuid4().hex
        
        message = {
            "seq": seq,
            "cmd": "logout",
            "data": {
                "deviceId": device_id
            }
        }
        
        if self._use_proto:
            try:
                logout_msg = self.yunhu_pb2.WSLogout()
                logout_msg.seq = seq
                logout_msg.cmd = "logout"
                logout_msg.data.deviceId = device_id
                return logout_msg.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def deserialize_message(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        反序列化接收的消息
        
        Args:
            data: 原始消息数据
            
        Returns:
            解析后的消息字典,失败返回None
        """
        try:
            # 首先尝试JSON解析
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        
        if self._use_proto:
            try:
                # 尝试ProtoBuf解析
                push_msg = self.yunhu_pb2.PushMessage()
                push_msg.ParseFromString(data)
                
                # 转换为字典格式
                result = {
                    "type": "push_message",
                    "msg": {
                        "msg_id": push_msg.msg.msg_id,
                        "sender": {
                            "chat_id": push_msg.msg.sender.chat_id,
                            "chat_type": push_msg.msg.sender.chat_type,
                            "name": push_msg.msg.sender.name,
                        },
                        "chat_id": push_msg.msg.chat_id,
                        "chat_type": push_msg.msg.chat_type,
                        "content": {
                            "text": push_msg.msg.content.text
                        },
                        "content_type": push_msg.msg.content_type,
                        "timestamp": push_msg.msg.timestamp
                    }
                }
                return result
            except Exception as e:
                logger.error(f"ProtoBuf反序列化失败: {e}")
        
        logger.warning(f"无法解析消息数据: {data[:100]}")
        return None
    
    @property
    def is_proto_available(self) -> bool:
        """检查ProtoBuf是否可用"""
        return self._use_proto


# 全局序列化器实例
serializer = ProtoBufSerializer()
