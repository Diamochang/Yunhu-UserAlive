"""
数据库模型定义
使用 SQLite (兼容 LiteFS)
"""

CREATE_TABLES_SQL = """
-- 用户账户信息表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_encrypted BLOB NOT NULL,
    token TEXT,
    user_id TEXT,
    device_id TEXT,
    platform TEXT DEFAULT 'windows',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户配置表
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    auto_takeover_enabled BOOLEAN DEFAULT 0,
    takeover_start_time TEXT DEFAULT '2024/01/01 00:00:00',  -- 格式: YYYY/MM/DD HH:MM:SS
    takeover_end_time TEXT DEFAULT '2024/01/01 06:00:00',    -- 格式: YYYY/MM/DD HH:MM:SS
    takeover_weekdays TEXT DEFAULT '1,2,3,4,5,6,7',  -- 1=周一, 7=周日
    last_console_access TIMESTAMP,
    auto_final_farewell_delay INTEGER DEFAULT 0,
    global_final_farewell BOOLEAN DEFAULT 0,
    article_links TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 信任好友表
CREATE TABLE IF NOT EXISTS friends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    friend_chat_id TEXT NOT NULL,
    friend_name TEXT,
    encrypted_address TEXT,
    local_final_farewell BOOLEAN DEFAULT 0,
    farewell_message TEXT,  -- 自定义终别消息
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, friend_chat_id)
);

-- TOTP 密钥表
CREATE TABLE IF NOT EXISTS totp_secrets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    secret_key TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 运行日志表(可选,主要使用 logging 模块)
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 签到记录表
CREATE TABLE IF NOT EXISTS checkin_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    success BOOLEAN DEFAULT 0,
    error_message TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_settings_user_id ON settings(user_id);
CREATE INDEX IF NOT EXISTS idx_friends_user_id ON friends(user_id);
CREATE INDEX IF NOT EXISTS idx_friends_chat_id ON friends(friend_chat_id);
CREATE INDEX IF NOT EXISTS idx_totp_user_id ON totp_secrets(user_id);
CREATE INDEX IF NOT EXISTS idx_checkin_user_id ON checkin_records(user_id);
CREATE INDEX IF NOT EXISTS idx_checkin_time ON checkin_records(checkin_time);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_yunhu_id ON users(user_id);
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_settings_last_access ON settings(last_console_access);
"""
