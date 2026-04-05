"""
Flask Web 控制台路由
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pyotp
import logging
from datetime import datetime

from database.db_manager import DatabaseManager
from auth.crypto import CryptoManager
from auth.totp import TOTPManager
from config import (
    MASTER_PASSWORD,
    FLASK_SECRET_KEY,
    YUNHU_API_BASE_URL,
    YUNHU_WS_URL,
    CHECKIN_BOT_ID,
    CHECKIN_GROUP_ID,
    CHECKIN_DELAY_MIN,
    CHECKIN_DELAY_MAX,
    DEPLOYMENT_ENV,
    YUNHU_EMAIL,
    YUNHU_PASSWORD,
    DEVICE_ID,
    PLATFORM,
    PROJECT_ROOT,
    validate_config
)

logger = logging.getLogger(__name__)


def create_app(scheduler=None, ws_client=None):
    """创建 Flask 应用"""
    app = Flask(__name__)
    app.secret_key = FLASK_SECRET_KEY
    
    db = DatabaseManager()
    crypto = CryptoManager()
    
    # 登录页面
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                return render_template('login.html', error='邮箱和密码不能为空')
            
            # 使用 authenticate_user 进行验证(支持 bcrypt)
            user = db.authenticate_user(email, password)
            
            if not user:
                return render_template('login.html', error='邮箱或密码错误')
            
            session['user_id'] = user['id']
            session['email'] = user['email']
            
            # 更新最后访问时间
            db.update_last_console_access(user['id'])
            
            logger.info(f"用户 {email} 登录成功")
            return redirect(url_for('dashboard'))
        
        return render_template('login.html')
    
    # 仪表板
    @app.route('/')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = db.get_user_by_id(session['user_id'])
        settings = db.get_user_settings(session['user_id'])
        last_checkin = db.get_last_checkin(session['user_id'])
        
        return render_template('dashboard.html', 
                                     user=user, 
                                     settings=settings,
                                     last_checkin=last_checkin)
    
    # 设置页面
    @app.route('/settings', methods=['GET', 'POST'])
    def settings():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add_article':
                title = request.form.get('article_title')
                url = request.form.get('article_url')
                
                if title and url:
                    db.add_article_link(session['user_id'], title, url)
                    logger.info(f"添加文章: {title}")
            
            elif action == 'add_friend':
                friend_chat_id = request.form.get('friend_chat_id')
                friend_name = request.form.get('friend_name')
                address = request.form.get('address')
                local_farewell = request.form.get('local_final_farewell') == 'on'
                farewell_message = request.form.get('farewell_message', '').strip() or None
                
                if friend_chat_id and address:
                    # 使用OpenPGP加密住址(用户自行加密后填写)
                    # 这里直接存储用户输入的密文
                    db.add_friend(session['user_id'], friend_chat_id, friend_name, 
                                 address, local_farewell, farewell_message)
                    logger.info(f"添加好友: {friend_name}")
            
            elif action == 'set_farewell_delay':
                delay_hours = int(request.form.get('delay_hours', 0))
                delay_seconds = delay_hours * 3600
                
                password = request.form.get('password')
                user = db.get_user_by_id(session['user_id'])
                
                try:
                    stored_password = crypto.decrypt(user['password_encrypted'])
                    if stored_password == password:
                        db.set_auto_final_farewell_delay(session['user_id'], delay_seconds)
                        logger.info(f"设置电子终别延迟: {delay_hours}小时")
                    else:
                        return render_template('settings.html', 
                                                     error='密码验证失败',
                                                     settings=db.get_user_settings(session['user_id']),
                                                     friends=db.get_friends(session['user_id']),
                                                     article_links=db.get_article_links(session['user_id']))
                except Exception as e:
                    logger.error(f"密码验证异常: {str(e)}")
                    return render_template('settings.html', 
                                                 error='验证失败',
                                                 settings=db.get_user_settings(session['user_id']),
                                                 friends=db.get_friends(session['user_id']),
                                                 article_links=db.get_article_links(session['user_id']))
            
            return redirect(url_for('settings'))
        
        # GET 请求
        settings_data = db.get_user_settings(session['user_id'])
        friends = db.get_friends(session['user_id'])
        articles = db.get_article_links(session['user_id'])
        
        return render_template('settings.html', 
                                     settings=settings_data,
                                     friends=friends, 
                                     article_links=articles)
    
    # API: 获取状态
    @app.route('/api/status')
    def api_status():
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        status_data = {
            'websocket_connected': ws_client.connected if ws_client else False,
            'scheduler_running': scheduler.scheduler.running if scheduler else False,
            'timestamp': datetime.now().isoformat()
        }
        
        # 添加 ProtoBuf 状态
        if ws_client:
            try:
                stats = ws_client.get_stats()
                status_data['proto'] = stats.get('proto_status', {})
            except Exception as e:
                logger.error(f"获取 ProtoBuf 状态失败: {e}")
        
        return jsonify(status_data)
    
    # API: 手动签到
    @app.route('/api/checkin', methods=['POST'])
    def api_manual_checkin():
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        if scheduler:
            scheduler.trigger_checkin_now()
            return jsonify({'success': True, 'message': '签到任务已触发'})
        
        return jsonify({'success': False, 'message': '调度器未初始化'}), 500
    
    # API: 更新托管设置
    @app.route('/api/takeover_settings', methods=['POST'])
    def api_update_takeover_settings():
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        try:
            data = request.get_json()
            enabled = data.get('enabled', False)
            start_time = data.get('start_time', '00:00')
            end_time = data.get('end_time', '06:00')
            weekdays = data.get('weekdays', [1,2,3,4,5,6,7])  # 默认全部
            
            # 将星期列表转换为字符串
            weekdays_str = ','.join(str(d) for d in weekdays)
            
            db.update_takeover_settings(
                session['user_id'], 
                enabled, 
                start_time, 
                end_time,
                weekdays_str
            )
            
            logger.info(f"用户 {session['email']} 更新托管设置: 启用={enabled}, 时间={start_time}-{end_time}, 星期={weekdays_str}")
            
            return jsonify({
                'success': True,
                'message': '托管设置已更新'
            })
        except Exception as e:
            logger.error(f"更新托管设置失败: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'更新失败: {str(e)}'
            }), 500
    
    # ==================== 健康检查和监控端点 ====================
    
    @app.route('/health')
    def health_check():
        """健康检查端点(无需认证)"""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "components": {
                "database": "unknown",
                "websocket": "unknown",
                "scheduler": "unknown"
            }
        }
        
        # 检查数据库
        try:
            db.get_user_count()
            health_status["components"]["database"] = "healthy"
        except Exception as e:
            health_status["components"]["database"] = f"unhealthy: {str(e)}"
            health_status["status"] = "degraded"
        
        # 检查WebSocket连接
        if ws_client:
            if ws_client.connected:
                health_status["components"]["websocket"] = "connected"
            else:
                health_status["components"]["websocket"] = "disconnected"
                health_status["status"] = "degraded"
        
        # 检查定时任务
        if scheduler:
            if scheduler.running:
                health_status["components"]["scheduler"] = "running"
            else:
                health_status["components"]["scheduler"] = "stopped"
                health_status["status"] = "degraded"
        
        # 根据状态返回不同的HTTP状态码
        status_code = 200 if health_status["status"] == "healthy" else 503
        return jsonify(health_status), status_code
    
    @app.route('/metrics')
    def metrics():
        """性能指标端点(Prometheus格式)"""
        metrics_data = []
        
        # WebSocket统计
        if ws_client:
            stats = ws_client.get_stats()
            metrics_data.append(f'# HELP websocket_messages_sent Total messages sent via WebSocket')
            metrics_data.append(f'# TYPE websocket_messages_sent counter')
            metrics_data.append(f'websocket_messages_sent {stats["messages_sent"]}')
            
            metrics_data.append(f'# HELP websocket_messages_received Total messages received via WebSocket')
            metrics_data.append(f'# TYPE websocket_messages_received counter')
            metrics_data.append(f'websocket_messages_received {stats["messages_received"]}')
            
            metrics_data.append(f'# HELP websocket_reconnections Total WebSocket reconnections')
            metrics_data.append(f'# TYPE websocket_reconnections counter')
            metrics_data.append(f'websocket_reconnections {stats["reconnections"]}')
            
            metrics_data.append(f'# HELP websocket_uptime_seconds WebSocket uptime in seconds')
            metrics_data.append(f'# TYPE websocket_uptime_seconds gauge')
            metrics_data.append(f'websocket_uptime_seconds {stats["uptime_seconds"]:.2f}')
            
            metrics_data.append(f'# HELP websocket_connected Whether WebSocket is connected (1=connected, 0=disconnected)')
            metrics_data.append(f'# TYPE websocket_connected gauge')
            metrics_data.append(f'websocket_connected {1 if ws_client.connected else 0}')
        
        # 数据库统计
        try:
            user_count = db.get_user_count()
            metrics_data.append(f'# HELP database_users_total Total number of users')
            metrics_data.append(f'# TYPE database_users_total gauge')
            metrics_data.append(f'database_users_total {user_count}')
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
        
        return '\n'.join(metrics_data), 200, {'Content-Type': 'text/plain'}
    
    @app.route('/api/status')
    def api_status():
        """API状态查询(需要认证)"""
        if 'user_id' not in session:
            return jsonify({"error": "未认证"}), 401
        
        status = {
            "user_id": session['user_id'],
            "timestamp": datetime.now().isoformat()
        }
        
        # WebSocket状态
        if ws_client:
            status["websocket"] = ws_client.get_stats()
        
        return jsonify(status)
    
    # API: 更新好友终别消息
    @app.route('/api/friend/farewell_message', methods=['POST'])
    def api_update_farewell_message():
        """更新好友的自定义终别消息"""
        if 'user_id' not in session:
            return jsonify({"error": "未认证"}), 401
        
        try:
            data = request.get_json()
            friend_chat_id = data.get('friend_chat_id')
            farewell_message = data.get('farewell_message', '').strip() or None
            
            if not friend_chat_id:
                return jsonify({"error": "缺少 friend_chat_id"}), 400
            
            db.update_farewell_message(session['user_id'], friend_chat_id, farewell_message)
            logger.info(f"用户 {session['email']} 更新了好友 {friend_chat_id} 的终别消息")
            
            return jsonify({
                "success": True,
                "message": "终别消息已更新",
                "farewell_message": farewell_message
            })
        except Exception as e:
            logger.error(f"更新终别消息失败: {e}")
            return jsonify({"error": str(e)}), 500
    
    return app
