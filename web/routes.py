"""
Flask Web 控制台路由
"""

from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
import pyotp
import logging
from datetime import datetime

from database.db_manager import DatabaseManager
from auth.crypto import CryptoManager
from auth.totp import TOTPManager

logger = logging.getLogger(__name__)


def create_app(scheduler=None, ws_client=None):
    """创建 Flask 应用"""
    app = Flask(__name__)
    app.secret_key = 'yunhu-useralive-secret-key-change-in-production'
    
    db = DatabaseManager()
    crypto = CryptoManager()
    
    # 登录页面
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                return render_template_string(LOGIN_TEMPLATE, error='邮箱和密码不能为空')
            
            # 使用 authenticate_user 进行验证(支持 bcrypt)
            user = db.authenticate_user(email, password)
            
            if not user:
                return render_template_string(LOGIN_TEMPLATE, error='邮箱或密码错误')
            
            session['user_id'] = user['id']
            session['email'] = user['email']
            
            # 更新最后访问时间
            db.update_last_console_access(user['id'])
            
            logger.info(f"用户 {email} 登录成功")
            return redirect(url_for('dashboard'))
        
        return render_template_string(LOGIN_TEMPLATE)
    
    # 仪表板
    @app.route('/')
    def dashboard():
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        user = db.get_user_by_id(session['user_id'])
        settings = db.get_user_settings(session['user_id'])
        last_checkin = db.get_last_checkin(session['user_id'])
        
        return render_template_string(DASHBOARD_TEMPLATE, 
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
                
                if friend_chat_id and address:
                    encrypted_address = crypto.encrypt(address)
                    db.add_friend(session['user_id'], friend_chat_id, friend_name, 
                                 encrypted_address)
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
                        return render_template_string(SETTINGS_TEMPLATE, 
                                                     error='密码验证失败',
                                                     settings=db.get_user_settings(session['user_id']),
                                                     friends=db.get_friends(session['user_id']),
                                                     articles=db.get_article_links(session['user_id']))
                except Exception as e:
                    logger.error(f"密码验证异常: {str(e)}")
                    return render_template_string(SETTINGS_TEMPLATE, 
                                                 error='验证失败',
                                                 settings=db.get_user_settings(session['user_id']),
                                                 friends=db.get_friends(session['user_id']),
                                                 articles=db.get_article_links(session['user_id']))
            
            return redirect(url_for('settings'))
        
        # GET 请求
        settings_data = db.get_user_settings(session['user_id'])
        friends = db.get_friends(session['user_id'])
        articles = db.get_article_links(session['user_id'])
        
        return render_template_string(SETTINGS_TEMPLATE, 
                                     settings=settings_data,
                                     friends=friends, 
                                     articles=articles)
    
    # API: 获取状态
    @app.route('/api/status')
    def api_status():
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        return jsonify({
            'websocket_connected': ws_client.connected if ws_client else False,
            'scheduler_running': scheduler.scheduler.running if scheduler else False,
            'timestamp': datetime.now().isoformat()
        })
    
    # API: 手动签到
    @app.route('/api/checkin', methods=['POST'])
    def api_manual_checkin():
        if 'user_id' not in session:
            return jsonify({'error': '未登录'}), 401
        
        if scheduler:
            scheduler.trigger_checkin_now()
            return jsonify({'success': True, 'message': '签到任务已触发'})
        
        return jsonify({'success': False, 'message': '调度器未初始化'}), 500
    
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
    
    return app


# ==================== HTML 模板 ====================

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>登录 - 云湖保活机器人</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 400px; margin: 50px auto; padding: 20px; }
        input { width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box; }
        button { width: 100%; padding: 10px; background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; }
    </style>
</head>
<body>
    <h2>云湖保活机器人 - 登录</h2>
    {% if error %}
    <p class="error">{{ error }}</p>
    {% endif %}
    <form method="POST">
        <input type="email" name="email" placeholder="邮箱" required>
        <input type="password" name="password" placeholder="密码" required>
        <button type="submit">登录</button>
    </form>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>仪表板 - 云湖保活机器人</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .status { display: inline-block; padding: 5px 10px; border-radius: 3px; }
        .status.online { background: #d4edda; color: #155724; }
        .status.offline { background: #f8d7da; color: #721c24; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>云湖保活机器人 - 仪表板</h1>
    
    <div class="card">
        <h3>用户信息</h3>
        <p>邮箱: {{ user.email }}</p>
        <p>平台: {{ user.platform }}</p>
    </div>
    
    <div class="card">
        <h3>运行状态</h3>
        <p>WebSocket: <span id="ws-status" class="status offline">检查中...</span></p>
        <p>定时任务: <span id="scheduler-status" class="status offline">检查中...</span></p>
        <p>最后签到: {{ last_checkin.checkin_time if last_checkin else '暂无记录' }}</p>
    </div>
    
    <div class="card">
        <h3>快速操作</h3>
        <button onclick="manualCheckin()">立即签到</button>
        <a href="/settings"><button style="margin-top: 10px;">进入设置</button></a>
    </div>
    
    <script>
        function updateStatus() {
            fetch('/api/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('ws-status').textContent = data.websocket_connected ? '在线' : '离线';
                    document.getElementById('ws-status').className = 'status ' + (data.websocket_connected ? 'online' : 'offline');
                    
                    document.getElementById('scheduler-status').textContent = data.scheduler_running ? '运行中' : '已停止';
                    document.getElementById('scheduler-status').className = 'status ' + (data.scheduler_running ? 'online' : 'offline');
                });
        }
        
        function manualCheckin() {
            fetch('/api/checkin', {method: 'POST'})
                .then(r => r.json())
                .then(data => alert(data.message));
        }
        
        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
"""

SETTINGS_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>设置 - 云湖保活机器人</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .card { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        input, select { padding: 8px; margin: 5px 0; width: 100%; box-sizing: border-box; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .error { color: red; }
        a { color: #007bff; }
    </style>
</head>
<body>
    <h1>设置</h1>
    
    {% if error %}
    <p class="error">{{ error }}</p>
    {% endif %}
    
    <div class="card">
        <h3>添加文章链接</h3>
        <form method="POST">
            <input type="hidden" name="action" value="add_article">
            <input type="text" name="article_title" placeholder="文章标题" required>
            <input type="url" name="article_url" placeholder="文章URL (如: yunhu://post-detail?id=xxx)" required>
            <button type="submit">添加</button>
        </form>
        
        <h4>已添加的文章:</h4>
        <ul>
        {% for article in articles %}
            <li>{{ article.title }} - {{ article.url }}</li>
        {% endfor %}
        </ul>
    </div>
    
    <div class="card">
        <h3>添加信任好友</h3>
        <form method="POST">
            <input type="hidden" name="action" value="add_friend">
            <input type="text" name="friend_chat_id" placeholder="好友云湖ID" required>
            <input type="text" name="friend_name" placeholder="备注名">
            <input type="text" name="address" placeholder="加密住址信息" required>
            <button type="submit">添加</button>
        </form>
        
        <h4>信任好友列表:</h4>
        <ul>
        {% for friend in friends %}
            <li>{{ friend.friend_name or friend.friend_chat_id }} (ID: {{ friend.friend_chat_id }})</li>
        {% endfor %}
        </ul>
    </div>
    
    <div class="card">
        <h3>电子终别自动开启延迟</h3>
        <form method="POST">
            <input type="hidden" name="action" value="set_farewell_delay">
            <input type="number" name="delay_hours" placeholder="延迟小时数 (0表示禁用)" min="0">
            <input type="password" name="password" placeholder="输入密码确认" required>
            <button type="submit">设置</button>
        </form>
        <p>当前延迟: {{ settings.auto_final_farewell_delay // 3600 if settings and settings.auto_final_farewell_delay else 0 }} 小时</p>
    </div>
    
    <p><a href="/">返回仪表板</a></p>
</body>
</html>
"""
