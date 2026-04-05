#!/usr/bin/env python3
"""
PythonAnywhere WSGI 入口文件
用于 Web 应用（仅提供 Web 控制台界面）

注意: WebSocket 和定时任务需要在 Always-on 任务中单独运行
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 设置环境
os.environ.setdefault('PYTHONANYWHERE', 'true')

from web.routes import create_app

# 创建 Flask 应用（不启动 WebSocket 和定时任务）
app = create_app(scheduler=None, ws_client=None)
