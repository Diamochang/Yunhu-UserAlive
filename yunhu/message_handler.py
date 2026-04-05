"""
消息处理器
处理接收到的消息,包括 @ 回复、住址查询等
"""

import json
import logging
import random
from typing import Dict, Any

from config import Config

logger = logging.getLogger(__name__)


class MessageHandler:
    """云湖消息处理器"""
    
    def __init__(self, ws_client, db_manager, crypto_manager):
        self.ws_client = ws_client
        self.db = db_manager
        self.crypto = crypto_manager
        # 建立云湖用户ID到本地用户ID的映射缓存
        self._user_id_map = {}  # {yunhu_user_id: local_user_id}
        self._build_user_id_map()
    
    def _build_user_id_map(self):
        """构建云湖用户ID到本地用户ID的映射"""
        try:
            users = self.db.get_all_users()
            for user in users:
                if user.get('user_id'):  # 云湖用户ID
                    self._user_id_map[user['user_id']] = user['id']
            logger.info(f"用户ID映射表已构建: {len(self._user_id_map)}个用户")
        except Exception as e:
            logger.error(f"构建用户ID映射失败: {str(e)}")
    
    def _get_local_user_id(self, yunhu_user_id: str) -> int:
        """
        根据云湖用户ID获取本地用户ID
        
        Args:
            yunhu_user_id: 云湖用户ID
            
        Returns:
            本地用户ID,如果找不到则返回None
        """
        # 先从缓存查找
        if yunhu_user_id in self._user_id_map:
            return self._user_id_map[yunhu_user_id]
        
        # 缓存未命中,从数据库查询
        user = self.db.get_user_by_yunhu_id(yunhu_user_id)
        if user:
            local_id = user['id']
            self._user_id_map[yunhu_user_id] = local_id
            logger.debug(f"用户ID映射: {yunhu_user_id} -> {local_id}")
            return local_id
        
        logger.warning(f"未找到云湖用户ID {yunhu_user_id} 对应的本地用户")
        return None
    
    def handle_message(self, message: Dict[str, Any]):
        """
        处理接收到的消息
        
        Args:
            message: 消息数据字典
        """
        try:
            cmd = message.get("cmd")
            data = message.get("data", {})
            
            if cmd == "newMsg" or cmd == "NewMsg":
                self._handle_new_message(data)
        
        except Exception as e:
            logger.error(f"消息处理失败: {str(e)}", exc_info=True)
    
    def _handle_new_message(self, data: Dict[str, Any]):
        """处理新消息"""
        try:
            chat_id = data.get("chat_id")
            chat_type = data.get("chat_type")
            sender = data.get("sender", {})
            sender_id = sender.get("chat_id") if isinstance(sender, dict) else None
            content = data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            if not sender_id or not text:
                return
            
            logger.debug(f"收到消息: 发送者={sender_id}, 类型={chat_type}, 内容={text[:50]}")
            
            # 检查是否被 @
            if self._is_mentioned(text):
                self._handle_mention(chat_id, chat_type, sender_id)
            
            # 检查是否为私聊且包含"住址"关键词
            if chat_type == 1 and "住址" in text:
                self._handle_address_request(chat_id, sender_id)
        
        except Exception as e:
            logger.error(f"处理新消息异常: {str(e)}", exc_info=True)
    
    def _is_mentioned(self, text: str) -> bool:
        """
        检查消息是否 @ 了当前用户
        云湖的 @ 格式通常是 @[用户名][用户ID]
        """
        user_id = self.ws_client.user_id
        if not user_id:
            return False
        
        # 检查多种可能的 @ 格式
        patterns = [
            f"[@{user_id}]",
            f"@{user_id}",
            f"@[{user_id}]",
        ]
        
        for pattern in patterns:
            if pattern in text:
                return True
        
        return False
    
    def _handle_mention(self, chat_id: str, chat_type: int, sender_id: str):
        """处理 @ 消息,发送随机文章链接"""
        try:
            # 确定使用哪个用户的配置
            # 策略1: 如果是群聊,使用机器人所属用户的配置
            # 策略2: 如果是私聊,尝试根据sender_id查找对应用户
            local_user_id = None
            
            if chat_type == 2:  # 群聊
                # 群聊中使用当前WebSocket连接的用户
                local_user_id = self._get_local_user_id(self.ws_client.user_id)
            elif chat_type == 1:  # 私聊
                # 私聊中尝试根据sender_id查找(假设sender也是已添加的用户)
                local_user_id = self._get_local_user_id(sender_id)
                # 如果sender不是注册用户,使用机器人用户
                if not local_user_id:
                    local_user_id = self._get_local_user_id(self.ws_client.user_id)
            
            if not local_user_id:
                logger.warning("无法确定使用哪个用户的配置,使用默认用户ID=1")
                local_user_id = 1
            
            # 获取用户设置
            settings = self.db.get_user_settings(local_user_id)
            
            if not settings or not settings['article_links']:
                logger.warning(f"用户 {local_user_id} 未配置文章链接")
                return
            
            # 从预设列表中随机选择一篇文章
            articles = json.loads(settings['article_links'])
            if not articles:
                logger.warning(f"用户 {local_user_id} 的文章列表为空")
                return
            
            selected_article = random.choice(articles)
            
            # 发送 Markdown 格式的文章链接
            markdown_text = f"【自动回复】\n[{selected_article['title']}]({selected_article['url']})"
            
            success = self.ws_client.send_markdown_message(chat_id, chat_type, markdown_text)
            
            if success:
                logger.info(f"已向 {sender_id} 发送文章链接: {selected_article['title']}")
            else:
                logger.error("发送文章链接失败")
        
        except Exception as e:
            logger.error(f"处理 @ 消息异常: {str(e)}", exc_info=True)
    
    def _handle_address_request(self, chat_id: str, sender_id: str):
        """处理住址查询请求"""
        try:
            # 确定使用哪个用户的信任好友列表
            # 通常住址查询是私聊,使用当前WebSocket用户的配置
            local_user_id = self._get_local_user_id(self.ws_client.user_id)
            
            if not local_user_id:
                logger.warning("无法确定用户ID,使用默认用户ID=1")
                local_user_id = 1
            
            # 获取好友信息
            friend = self.db.get_friend_by_chat_id(local_user_id, sender_id)
            
            if not friend:
                logger.info(f"好友 {sender_id} 不在用户 {local_user_id} 的信任列表中")
                return
            
            if not friend['encrypted_address']:
                logger.warning(f"好友 {sender_id} 未设置加密住址")
                return
            
            # 直接使用用户存储的OpenPGP密文(不再解密)
            encrypted_address = friend['encrypted_address']
            
            # 检查是否有局部电子终别标记
            farewell_msg = ""
            if friend['local_final_farewell']:
                # 使用自定义终别消息，如果没有则使用默认消息
                custom_message = friend.get('farewell_message')
                if custom_message:
                    farewell_msg = f"\n\n⚠️【电子终别】{custom_message}"
                else:
                    farewell_msg = "\n\n⚠️【电子终别】特别提醒：请在信封上写明你的实际名址，以免失去最后的联系。"
            
            # 发送加密住址信息
            response_text = f"【自动回复】加密住址信息（请使用您的OpenPGP私钥解密）：\n\n{encrypted_address}{farewell_msg}"
            
            success = self.ws_client.send_text_message(chat_id, 1, response_text)
            
            if success:
                logger.info(f"已向好友 {sender_id} 发送加密住址")
            else:
                logger.error("发送住址信息失败")
        
        except Exception as e:
            logger.error(f"处理住址请求异常: {str(e)}", exc_info=True)
