"""
定时任务模块
管理签到、电子终别检查等定时任务
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import random
import datetime
import logging
from typing import Optional

from config import (
    CHECKIN_BOT_ID,
    CHECKIN_GROUP_ID,
    CHECKIN_DELAY_MIN,
    CHECKIN_DELAY_MAX
)

logger = logging.getLogger(__name__)


class TaskScheduler:
    """定时任务调度器"""
    
    def __init__(self, ws_client, db_manager):
        self.scheduler = BackgroundScheduler()
        self.ws_client = ws_client
        self.db = db_manager
        self._last_checkin_time = None
    
    def start(self):
        """启动调度器"""
        # 每日凌晨 00:00 触发签到(实际执行时间会随机延迟 0-5 分钟)
        self.scheduler.add_job(
            func=self.daily_checkin,
            trigger=CronTrigger(hour=0, minute=0),
            id='daily_checkin',
            name='每日签到',
            misfire_grace_time=300  # 允许 5 分钟误差
        )
        
        # 每分钟检查电子终别自动开启
        self.scheduler.add_job(
            func=self.check_final_farewell,
            trigger='interval',
            minutes=1,
            id='check_final_farewell',
            name='检查电子终别'
        )
        
        self.scheduler.start()
        logger.info("定时任务调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.scheduler.shutdown()
        logger.info("定时任务调度器已停止")
    
    def daily_checkin(self):
        """每日签到任务"""
        try:
            # 检查是否在托管时间内
            if not self.db.is_in_takeover_time(1):  # 默认用户ID=1
                logger.info("当前不在自动托管时间内,跳过签到")
                return
                
            logger.info("开始执行签到任务...")
                
            success_count = 0
            total_tasks = 3
                
            # 1. HXBOT 普通签到 (发送 /签到 到机器人 ID: 45059971)
            if self.ws_client.send_text_message(
                bot_id=CHECKIN_BOT_ID,
                chat_type=3,  # 机器人
                text="/签到"
            ):
                logger.info("✓ HXBOT 普通签到完成")
                success_count += 1
            else:
                logger.error("✗ HXBOT 普通签到失败")
                
            # 短暂延迟,避免发送过快
            import time
            time.sleep(2)
                
            # 2. 鹿管签到 (发送 /鹿)
            if self.ws_client.send_text_message(
                bot_id=CHECKIN_BOT_ID,
                chat_type=3,
                text="/鹿"
            ):
                logger.info("✓ 鹿管签到完成")
                success_count += 1
            else:
                logger.error("✗ 鹿管签到失败")
                
            time.sleep(2)
                
            # 3. 有一城群聊签到 (群聊 ID: 679137839, 发送“签到”/“打卡”/“冒泡”之一)
            checkin_words = ["签到", "打卡", "冒泡"]
            word = random.choice(checkin_words)
                
            if self.ws_client.send_text_message(
                group_id=CHECKIN_GROUP_ID,
                chat_type=2,  # 群聊
                text=word
            ):
                logger.info(f"✓ 有一城群聊签到完成 (发送: {word})")
                success_count += 1
            else:
                logger.error("✗ 有一城群聊签到失败")
                
            # 记录签到结果
            all_success = (success_count == total_tasks)
            self.db.record_checkin(
                user_id=1,  # 默认第一个用户
                success=all_success,
                error_message=None if all_success else f"成功 {success_count}/{total_tasks}"
            )
                
            self._last_checkin_time = datetime.datetime.now()
            
            if all_success:
                logger.info("=== 所有签到任务完成 ===")
            else:
                logger.warning(f"=== 签到任务部分失败: {success_count}/{total_tasks} ===")
        
        except Exception as e:
            logger.error(f"签到任务异常: {str(e)}", exc_info=True)
            self.db.record_checkin(user_id=1, success=False, error_message=str(e))
    
    def check_final_farewell(self):
        """检查是否需要自动开启全局电子终别标记"""
        try:
            users = self.db.get_all_users_with_settings()
            now = datetime.datetime.now()
            
            for user in users:
                delay = user['auto_final_farewell_delay']
                last_access = user['last_console_access']
                
                if delay > 0 and last_access:
                    # 解析最后访问时间
                    if isinstance(last_access, str):
                        last_access_time = datetime.datetime.fromisoformat(last_access)
                    else:
                        last_access_time = last_access
                    
                    elapsed = (now - last_access_time).total_seconds()
                    
                    if elapsed >= delay:
                        # 自动开启全局电子终别
                        self.db.set_global_final_farewell(user['id'], True)
                        # 同时开启自动托管
                        self.db.set_auto_takeover(user['id'], True)
                        
                        logger.info(f"用户 {user['email']} 已自动开启全局电子终别标记和自动托管")
        
        except Exception as e:
            logger.error(f"检查电子终别异常: {str(e)}", exc_info=True)
    
    def get_last_checkin_time(self) -> Optional[datetime.datetime]:
        """获取最后一次签到时间"""
        return self._last_checkin_time
    
    def trigger_checkin_now(self):
        """立即触发签到(用于手动测试)"""
        logger.info("手动触发签到任务")
        import threading
        thread = threading.Thread(target=self.daily_checkin, daemon=True)
        thread.start()
