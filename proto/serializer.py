"""
ProtoBuf消息序列化工具
用于云湖WebSocket消息的序列化和反序列化
"""
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ProtoBufSerializer:
    """ProtoBuf消息序列化器
    
    云湖API支持情况:
    - 大多数用户API: 必须使用ProtoBuf
    - 部分新API: 仅支持JSON
    
    本序列化器会根据实际情况自动选择最佳格式,
    并在ProtoBuf不可用时降级到JSON。
    """
    
    def __init__(self):
        self._use_proto = False
        self._proto_errors = {}  # 记录哪些消息类型ProtoBuf失败
        try:
            # 尝试导入编译后的proto文件
            from proto.generated import yunhu_pb2
            self.yunhu_pb2 = yunhu_pb2
            self._use_proto = True
            logger.info("✓ ProtoBuf支持已启用")
            logger.info("  提示: 大多数云湖API需要ProtoBuf,部分新API使用JSON")
        except ImportError as e:
            logger.warning(f"⚠ ProtoBuf模块未找到,将使用JSON格式: {e}")
            logger.warning("  重要: 某些云湖API可能需要ProtoBuf才能正常工作")
            logger.warning("  建议运行: bash proto/compile.sh 启用ProtoBuf支持")
    
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
                error_key = "WSLogin"
                if error_key not in self._proto_errors:
                    self._proto_errors[error_key] = str(e)
                    logger.warning(f"⚠ ProtoBuf序列化失败 [{error_key}],回退到JSON: {e}")
        
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
    
    def serialize_edit_message(self, msg_id: str, chat_id: str, chat_type: int,
                               text: str, content_type: int = 1,
                               quote_msg_id: str = None) -> bytes:
        """
        序列化编辑消息请求
        
        Args:
            msg_id: 消息ID
            chat_id: 聊天对象ID
            chat_type: 聊天类型(1-用户, 2-群聊, 3-机器人)
            text: 消息文本
            content_type: 内容类型(1-文本, 3-Markdown, 8-HTML)
            quote_msg_id: 引用消息ID(可选)
            
        Returns:
            序列化后的消息
        """
        message = {
            "msg_id": msg_id,
            "chat_id": chat_id,
            "chat_type": chat_type,
            "content": {
                "text": text
            },
            "content_type": content_type
        }
        
        if quote_msg_id:
            message["quote_msg_id"] = quote_msg_id
        
        if self._use_proto:
            try:
                edit_msg = self.yunhu_pb2.EditMessageRequest()
                edit_msg.msg_id = msg_id
                edit_msg.chat_id = chat_id
                edit_msg.chat_type = chat_type
                edit_msg.content.text = text
                edit_msg.content_type = content_type
                if quote_msg_id:
                    edit_msg.quote_msg_id = quote_msg_id
                return edit_msg.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def serialize_recall_message(self, msg_id: str, chat_id: str, chat_type: int) -> bytes:
        """
        序列化撤回消息请求
        
        Args:
            msg_id: 消息ID
            chat_id: 聊天对象ID
            chat_type: 聊天类型(1-用户, 2-群聊, 3-机器人)
            
        Returns:
            序列化后的消息
        """
        import uuid
        seq = uuid.uuid4().hex
        
        message = {
            "seq": seq,
            "cmd": "recallMsg",
            "data": {
                "msgId": msg_id,
                "chatId": chat_id,
                "chatType": chat_type
            }
        }
        
        if self._use_proto:
            try:
                recall_msg = self.yunhu_pb2.RecallMessageRequest()
                recall_msg.msg_id = msg_id
                recall_msg.chat_id = chat_id
                recall_msg.chat_type = chat_type
                return recall_msg.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def serialize_batch_recall_message(self, msg_ids: list, chat_id: str, chat_type: int) -> bytes:
        """
        序列化批量撤回消息请求
        
        Args:
            msg_ids: 消息ID列表
            chat_id: 聊天对象ID
            chat_type: 聊天类型
            
        Returns:
            序列化后的消息
        """
        import uuid
        seq = uuid.uuid4().hex
        
        message = {
            "seq": seq,
            "cmd": "batchRecallMsg",
            "data": {
                "msgIds": msg_ids,
                "chatId": chat_id,
                "chatType": chat_type
            }
        }
        
        if self._use_proto:
            try:
                batch_recall = self.yunhu_pb2.BatchRecallMessageRequest()
                batch_recall.msg_id.extend(msg_ids)
                batch_recall.chat_id = chat_id
                batch_recall.chat_type = chat_type
                return batch_recall.SerializeToString()
            except Exception as e:
                logger.error(f"ProtoBuf序列化失败,回退到JSON: {e}")
        
        return json.dumps(message).encode('utf-8')
    
    def serialize_button_report(self, msg_id: str, chat_type: int, 
                                chat_id: str, user_id: str, button_value: str) -> bytes:
        """
        序列化按钮事件报告
        
        Args:
            msg_id: 消息ID
            chat_type: 聊天类型
            chat_id: 聊天对象ID
            user_id: 用户ID
            button_value: 按钮值
            
        Returns:
            序列化后的消息
        """
        import uuid
        seq = uuid.uuid4().hex
        
        message = {
            "seq": seq,
            "cmd": "buttonReport",
            "data": {
                "msgId": msg_id,
                "chatType": chat_type,
                "chatId": chat_id,
                "userId": user_id,
                "buttonValue": button_value
            }
        }
        
        if self._use_proto:
            try:
                button_report = self.yunhu_pb2.ButtonReportRequest()
                button_report.msg_id = msg_id
                button_report.chat_type = chat_type
                button_report.chat_id = chat_id
                button_report.user_id = user_id
                button_report.button_value = button_value
                return button_report.SerializeToString()
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
    
    def get_proto_errors(self) -> dict:
        """
        获取ProtoBuf序列化错误统计
        
        Returns:
            字典,键为消息类型,值为错误信息
        """
        return self._proto_errors.copy()
    
    def clear_proto_errors(self):
        """清除ProtoBuf错误记录"""
        self._proto_errors.clear()
        logger.info("ProtoBuf错误记录已清除")
    
    def get_status_report(self) -> dict:
        """
        获取序列化器状态报告
        
        Returns:
            包含状态信息的字典
        """
        return {
            "proto_available": self._use_proto,
            "proto_errors_count": len(self._proto_errors),
            "proto_errors": self._proto_errors.copy(),
            "fallback_mode": "JSON" if not self._use_proto or self._proto_errors else "ProtoBuf"
        }


# 全局序列化器实例
serializer = ProtoBufSerializer()
