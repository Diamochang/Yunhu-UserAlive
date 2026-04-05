#!/usr/bin/env python3
"""
PythonAnywhere 部署检查脚本
用于验证部署是否正确配置
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def check_environment():
    """检查配置文件"""
    print("\n" + "=" * 60)
    print("1. 配置文件检查")
    print("=" * 60)
    
    # 检查 config.py 文件
    config_file = os.path.join(project_root, 'config.py')
    if not os.path.exists(config_file):
        print(f"❌ 配置文件不存在: {config_file}")
        print(f"   提示: 请复制 config_local.py.example 为 config.py")
        return False
    
    print(f"✅ 配置文件存在")
    
    # 验证配置
    try:
        from config import (
            MASTER_PASSWORD,
            ENCRYPTION_SALT,
            FLASK_SECRET_KEY,
            DEPLOYMENT_ENV
        )
        
        # 检查必需的配置
        all_ok = True
        if not MASTER_PASSWORD or len(MASTER_PASSWORD) < 8:
            print(f"❌ MASTER_PASSWORD: 长度不足 8 个字符")
            all_ok = False
        else:
            print(f"✅ MASTER_PASSWORD: 已设置（{len(MASTER_PASSWORD)} 字符）")
        
        if not ENCRYPTION_SALT:
            print(f"❌ ENCRYPTION_SALT: 未设置")
            all_ok = False
        else:
            print(f"✅ ENCRYPTION_SALT: 已设置（{len(ENCRYPTION_SALT)} 字符）")
        
        if not FLASK_SECRET_KEY:
            print(f"❌ FLASK_SECRET_KEY: 未设置")
            all_ok = False
        else:
            print(f"✅ FLASK_SECRET_KEY: 已设置（{len(FLASK_SECRET_KEY)} 字符）")
        
        # 检查部署环境
        if DEPLOYMENT_ENV not in ["local", "pythonanywhere"]:
            print(f"❌ DEPLOYMENT_ENV: 必须是 'local' 或 'pythonanywhere'")
            all_ok = False
        else:
            print(f"✅ DEPLOYMENT_ENV: {DEPLOYMENT_ENV}")
        
        return all_ok
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False

def check_database():
    """检查数据库配置"""
    print("\n" + "=" * 60)
    print("2. 数据库检查")
    print("=" * 60)
    
    from config import DATABASE_PATH
    db_path = DATABASE_PATH
    
    print(f"数据库路径: {db_path}")
    
    # 检查数据库目录
    db_dir = os.path.dirname(db_path)
    if db_dir and os.path.exists(db_dir):
        print(f"✅ 数据库目录存在: {db_dir}")
    elif db_dir:
        print(f"⚠️  数据库目录不存在: {db_dir}")
        print(f"   提示: 系统会自动创建")
    else:
        print(f"⚠️  使用当前目录: {os.getcwd()}")
    
    # 检查数据库文件
    if os.path.exists(db_path):
        print(f"✅ 数据库文件存在")
        
        # 尝试连接
        try:
            from database.db_manager import DatabaseManager
            db = DatabaseManager()
            
            # 测试连接
            with db.get_connection() as conn:
                result = conn.execute("SELECT COUNT(*) FROM users").fetchone()
                user_count = result[0] if result else 0
                print(f"✅ 数据库连接成功, 用户数: {user_count}")
                
                if user_count == 0:
                    print(f"⚠️  提示: 需要添加用户配置")
                
                return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {e}")
            return False
    else:
        print(f"⚠️  数据库文件不存在（首次运行会自动创建）")
        return True

def check_dependencies():
    """检查依赖安装"""
    print("\n" + "=" * 60)
    print("3. 依赖检查")
    print("=" * 60)
    
    required_packages = [
        ('flask', 'Flask'),
        ('websocket', 'websocket-client'),
        ('apscheduler', 'APScheduler'),
        ('cryptography', 'cryptography'),
        ('bcrypt', 'bcrypt'),
        ('pyotp', 'pyotp'),
        ('requests', 'requests'),
    ]
    
    all_ok = True
    for module, name in required_packages:
        try:
            __import__(module)
            print(f"✅ {name}: 已安装")
        except ImportError:
            print(f"❌ {name}: 未安装")
            all_ok = False
    
    # 检查 ProtoBuf（可选）
    try:
        from proto.generated import yunhu_pb2
        print(f"✅ ProtoBuf: 已编译")
    except ImportError:
        print(f"⚠️  ProtoBuf: 未编译（建议运行 bash proto/compile.sh）")
    
    return all_ok

def check_paths():
    """检查路径配置"""
    print("\n" + "=" * 60)
    print("4. 路径检查")
    print("=" * 60)
    
    from config import LOG_FILE, DEPLOYMENT_ENV
    
    # 检查日志文件路径
    log_file = LOG_FILE
    log_dir = os.path.dirname(log_file)
    
    print(f"日志文件: {log_file}")
    
    if log_dir and os.path.exists(log_dir):
        print(f"✅ 日志目录存在")
    elif log_dir:
        print(f"⚠️  日志目录不存在")
        print(f"   提示: 系统会自动创建")
    
    # 检查部署环境
    print(f"部署环境: {DEPLOYMENT_ENV}")
    
    # 检查 WSGI 文件
    wsgi_file = os.path.join(project_root, 'wsgi.py')
    if os.path.exists(wsgi_file):
        print(f"✅ WSGI 文件存在: {wsgi_file}")
    else:
        print(f"❌ WSGI 文件不存在: {wsgi_file}")
    
    # 检查 Always-on 脚本
    always_on_file = os.path.join(project_root, 'always_on.py')
    if os.path.exists(always_on_file):
        print(f"✅ Always-on 脚本存在: {always_on_file}")
    else:
        print(f"❌ Always-on 脚本不存在: {always_on_file}")
    
    return True

def check_web_app():
    """检查 Web 应用配置"""
    print("\n" + "=" * 60)
    print("5. Web 应用检查")
    print("=" * 60)
    
    try:
        from web.routes import create_app
        from config import FLASK_SECRET_KEY
        
        # 创建测试应用
        app = create_app(scheduler=None, ws_client=None)
        
        print(f"✅ Flask 应用创建成功")
        print(f"   Secret Key: {'已设置' if FLASK_SECRET_KEY else '使用默认值'}")
        
        # 检查路由
        with app.test_client() as client:
            # 测试登录页面
            response = client.get('/login')
            if response.status_code == 200:
                print(f"✅ 登录路由: 正常")
            else:
                print(f"❌ 登录路由: 返回 {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Web 应用检查失败: {e}")
        return False

def check_network():
    """检查网络连接"""
    print("\n" + "=" * 60)
    print("6. 网络连接检查")
    print("=" * 60)
    
    from config import YUNHU_API_BASE_URL, YUNHU_WS_URL
    
    print(f"云湖 API: {YUNHU_API_BASE_URL}")
    print(f"WebSocket: {YUNHU_WS_URL}")
    
    try:
        import requests
        # 测试 API 连接
        response = requests.get(YUNHU_API_BASE_URL, timeout=5)
        print(f"✅ API 可访问: {response.status_code}")
        return True
    except Exception as e:
        print(f"⚠️  API 连接测试失败: {e}")
        print(f"   提示: 可能是网络限制，实际使用时需要连接")
        return True

def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Yunhu-UserAlive PythonAnywhere 部署检查")
    print("=" * 60)
    print(f"项目目录: {project_root}")
    print(f"Python 版本: {sys.version.split()[0]}")
    
    from config import DEPLOYMENT_ENV
    print(f"部署环境: {DEPLOYMENT_ENV}")
    
    # 运行所有检查
    checks = [
        ("配置文件", check_environment),
        ("数据库", check_database),
        ("依赖", check_dependencies),
        ("路径", check_paths),
        ("Web 应用", check_web_app),
        ("网络", check_network)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 检查失败: {e}")
            results.append((name, False))
    
    # 输出总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有检查通过! 部署配置正确。")
        return 0
    else:
        print("\n⚠️  存在问题，请根据上述提示修复。")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n检查已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n检查过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
