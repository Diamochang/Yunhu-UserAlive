#!/bin/bash
# Yunhu-UserAlive 快速启动脚本

echo "================================================"
echo "  Yunhu-UserAlive 快速启动"
echo "================================================"
echo ""

# 检查 Python3
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python 3.9+"
    exit 1
fi

echo "✅ Python3 已安装: $(python3 --version)"
echo ""

# 检查依赖
echo "📦 检查依赖..."
if python3 -c "import flask" 2>/dev/null; then
    echo "✅ Flask 已安装"
else
    echo "⚠️  Flask 未安装,正在安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
fi
echo ""

# 验证模板
echo "🔍 验证模板文件..."
python3 verify_templates.py
if [ $? -ne 0 ]; then
    echo "❌ 模板验证失败"
    exit 1
fi
echo ""

# 检查数据库
if [ ! -f "data/yunhu_useralive.db" ]; then
    echo "⚠️  数据库文件不存在"
    echo "请先运行初始化脚本创建用户"
    echo ""
    echo "示例:"
    echo "  python3 init_user.py"
    echo ""
    read -p "是否继续启动? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi
echo ""

# 启动服务器
echo "🚀 启动 Web 服务器..."
echo ""
echo "================================================"
echo "  服务器即将启动"
echo "  访问地址: http://localhost:5000"
echo "  按 Ctrl+C 停止服务器"
echo "================================================"
echo ""

python3 main.py
