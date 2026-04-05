#!/usr/bin/env python3
"""
Yunhu-UserAlive 初始化脚本

简化初始化流程，自动处理:
1. 配置验证
2. 数据库创建
3. 用户初始化
4. 数据迁移（如果需要）
"""

import os
import sys
import uuid
import secrets
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_step(step, description):
    """打印步骤"""
    print(f"\n[{step}] {description}")

def print_success(message):
    """打印成功消息"""
    print(f"✅ {message}")

def print_error(message):
    """打印错误消息"""
    print(f"❌ {message}")

def print_warning(message):
    """打印警告消息"""
    print(f"⚠️  {message}")

def check_config_file():
    """检查配置文件"""
    print_step(1, "检查配置文件")
    
    config_file = PROJECT_ROOT / "config.py"
    
    if config_file.exists():
        print_success("配置文件已存在")
        print(f"   路径: {config_file}")
        return True
    else:
        print_warning("配置文件不存在")
        print(f"   正在创建: {config_file}")
        
        # 复制示例文件
        example_file = PROJECT_ROOT / "config_local.py.example"
        if not example_file.exists():
            print_error("找不到配置示例文件")
            return False
        
        import shutil
        shutil.copy(example_file, config_file)
        print_success("配置文件已创建")
        return True

def validate_config():
    """验证配置"""
    print_step(2, "验证配置")
    
    try:
        from config import validate_config, DEPLOYMENT_ENV, PROJECT_ROOT
        
        validate_config()
        print_success("配置验证通过")
        print(f"   部署环境: {DEPLOYMENT_ENV}")
        print(f"   项目根目录: {PROJECT_ROOT}")
        
        return True
    except ValueError as e:
        print_error(f"配置验证失败")
        print(f"   错误: {e}")
        print(f"\n请编辑 config.py 文件，修正以下问题:")
        print(f"   {e}")
        return False
    except Exception as e:
        print_error(f"加载配置失败")
        print(f"   错误: {e}")
        return False

def init_database():
    """初始化数据库"""
    print_step(3, "初始化数据库")
    
    try:
        from database.db_manager import DatabaseManager
        
        db = DatabaseManager()
        db.init_db()
        print_success("数据库初始化成功")
        
        # 检查是否需要迁移
        check_migrations(db)
        
        return True
    except Exception as e:
        print_error(f"数据库初始化失败")
        print(f"   错误: {e}")
        return False

def check_migrations(db):
    """检查并执行数据库迁移"""
    print_step(4, "检查数据库迁移")
    
    try:
        # 检查是否需要添加 takeover_weekdays 字段
        with db.get_connection() as conn:
            cursor = conn.execute("PRAGMA table_info(settings)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'takeover_weekdays' not in columns:
                print_warning("检测到旧版本数据库，需要迁移...")
                print("   添加 takeover_weekdays 字段...")
                
                # SQLite 不支持直接添加带默认值的列
                # 需要重建表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS settings_new (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        auto_takeover_enabled BOOLEAN DEFAULT 0,
                        takeover_start_time TEXT DEFAULT '2024/01/01 00:00:00',
                        takeover_end_time TEXT DEFAULT '2024/01/01 06:00:00',
                        takeover_weekdays TEXT DEFAULT '1,2,3,4,5,6,7',
                        last_console_access TIMESTAMP,
                        auto_final_farewell_delay INTEGER DEFAULT 0,
                        global_final_farewell BOOLEAN DEFAULT 0,
                        article_links TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """)
                
                # 复制数据
                conn.execute("""
                    INSERT INTO settings_new 
                    SELECT id, user_id, auto_takeover_enabled,
                           takeover_start_time, takeover_end_time,
                           '1,2,3,4,5,6,7',
                           last_console_access, auto_final_farewell_delay,
                           global_final_farewell, article_links,
                           created_at, updated_at
                    FROM settings
                """)
                
                # 替换表
                conn.execute("DROP TABLE settings")
                conn.execute("ALTER TABLE settings_new RENAME TO settings")
                
                print_success("已添加 takeover_weekdays 字段")
            
            # 检查是否需要添加 farewell_message 字段
            cursor = conn.execute("PRAGMA table_info(friends)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'farewell_message' not in columns:
                print_warning("检测到旧版本数据库，需要迁移...")
                print("   添加 farewell_message 字段...")
                
                conn.execute("""
                    ALTER TABLE friends
                    ADD COLUMN farewell_message TEXT
                """)
                
                print_success("已添加 farewell_message 字段")
    
    except Exception as e:
        print_warning(f"数据库迁移检查失败: {e}")
        print("   继续执行...")

def init_user():
    """初始化用户"""
    print_step(5, "初始化云湖账户")
    
    try:
        from database.db_manager import DatabaseManager
        from auth.crypto import CryptoManager
        from config import YUNHU_EMAIL, YUNHU_PASSWORD, DEVICE_ID, PLATFORM
        
        db = DatabaseManager()
        crypto = CryptoManager()
        
        # 检查是否已有用户
        users = db.get_all_users()
        if users:
            print_warning(f"数据库中已有 {len(users)} 个用户")
            print("   如需重新初始化，请手动删除数据库文件后重试")
            return True
        
        # 获取用户信息
        print("\n请输入云湖账户信息:")
        print("（首次运行需要，信息将被加密存储）")
        
        # 使用配置文件中的值或提示输入
        email = YUNHU_EMAIL or input("邮箱地址: ").strip()
        password = YUNHU_PASSWORD or input("密码: ").strip()
        
        if not email or not password:
            print_error("邮箱和密码不能为空")
            return False
        
        # 生成设备 ID（如果未设置）
        device_id = DEVICE_ID or str(uuid.uuid4())
        platform = PLATFORM
        
        # 加密敏感信息
        email_encrypted = crypto.encrypt(email)
        password_encrypted = crypto.encrypt(password)
        
        # 添加用户
        user_id = db.add_user(
            email=email,
            password_encrypted=password_encrypted,
            device_id=device_id,
            platform=platform
        )
        
        print_success("云湖账户已添加")
        print(f"   用户 ID: {user_id}")
        print(f"   邮箱: {email}")
        print(f"   设备 ID: {device_id}")
        print(f"   平台: {platform}")
        
        # 测试解密
        print("\n测试解密...")
        decrypted_email = crypto.decrypt(email_encrypted)
        decrypted_password = crypto.decrypt(password_encrypted)
        
        if decrypted_email == email and decrypted_password == password:
            print_success("加密/解密测试通过")
        else:
            print_error("加密/解密测试失败")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"用户初始化失败")
        print(f"   错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_random_configs():
    """生成随机配置"""
    print_step(6, "生成随机配置（可选）")
    
    response = input("\n是否生成安全的随机配置？(y/n): ").strip().lower()
    
    if response == 'y':
        print("\n生成随机配置...")
        
        master_password = secrets.token_urlsafe(16)
        encryption_salt = secrets.token_hex(16)
        flask_secret_key = secrets.token_urlsafe(32)
        
        print("\n请将以下配置复制到 config.py 文件:")
        print("=" * 60)
        print(f"MASTER_PASSWORD = \"{master_password}\"")
        print(f"ENCRYPTION_SALT = \"{encryption_salt}\"")
        print(f"FLASK_SECRET_KEY = \"{flask_secret_key}\"")
        print("=" * 60)
        
        print("\n💡 提示: 你可以手动编辑 config.py 文件应用这些配置")
        print("   或按回车跳过，使用默认配置")
        
        input()

def create_init_mark():
    """创建初始化标记文件"""
    init_mark = PROJECT_ROOT / ".initialized"
    init_mark.write_text("This file marks that Yunhu-UserAlive has been initialized.")
    print_success("初始化标记文件已创建")

def main():
    """主函数"""
    print_header("Yunhu-UserAlive 初始化向导")
    
    print("""
本向导将帮助您完成以下步骤:
1. 检查配置文件
2. 验证配置
3. 初始化数据库
4. 检查数据库迁移
5. 初始化云湖账户
    """)
    
    input("按回车键开始...")
    
    # 执行初始化步骤
    steps = [
        ("检查配置文件", check_config_file),
        ("验证配置", validate_config),
        ("初始化数据库", init_database),
        ("初始化云湖账户", init_user),
    ]
    
    all_success = True
    for name, func in steps:
        try:
            if not func():
                all_success = False
                print_error(f"{name} 失败，初始化中止")
                break
        except KeyboardInterrupt:
            print_warning("\n用户取消")
            return 1
        except Exception as e:
            print_error(f"{name} 时发生未预期的错误")
            print(f"   错误: {e}")
            import traceback
            traceback.print_exc()
            all_success = False
            break
    
    if all_success:
        # 生成随机配置（可选）
        generate_random_configs()
        
        # 创建初始化标记
        create_init_mark()
        
        # 显示成功消息
        print_header("初始化完成！")
        print("""
✅ 所有步骤已完成！

下一步:

1. 本地开发:
   python app.py

2. PythonAnywhere 部署:
   参考 docs/PythonAnywhere快速开始.md

3. 启动后:
   访问 http://localhost:5000
   使用你刚才配置的邮箱和密码登录

配置文件:
   - config.py (所有配置)
   - data/yunhu_useralive.db (数据库)

如需修改配置，请编辑 config.py 文件。
        """)
        
        return 0
    else:
        print_header("初始化失败")
        print("""
❌ 初始化过程中遇到错误

请检查:
1. 配置文件 config.py 是否正确
2. 是否有足够的文件系统权限
3. Python 依赖是否已安装

如需帮助，请查看:
   - README.md
   - docs/PythonAnywhere快速开始.md
        """)
        
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n初始化已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n初始化过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
