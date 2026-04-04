#!/bin/bash
# 生产环境启动脚本

set -e

echo "=========================================="
echo "  云湖保活用户机器人 - 生产环境启动"
echo "=========================================="

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "错误: Python版本至少需要 $REQUIRED_VERSION,当前版本: $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python版本: $PYTHON_VERSION"

# 检查.env文件
if [ ! -f .env ]; then
    echo "⚠️  警告: .env 文件不存在"
    echo "正在从 .env.example 创建..."
    cp .env.example .env
    echo "请编辑 .env 文件并设置必要的环境变量"
    exit 1
fi

# 安装依赖
echo ""
echo "📦 安装依赖包..."
pip install -r requirements.txt --quiet

# 编译ProtoBuf(如果protoc可用)
echo ""
echo "🔧 检查ProtoBuf编译器..."
if command -v protoc &> /dev/null; then
    echo "编译ProtoBuf文件..."
    bash proto/compile.sh || echo "⚠️  ProtoBuf编译失败,将使用JSON格式"
else
    echo "⚠️  未找到protoc编译器,将使用JSON格式"
    echo "   如需启用ProtoBuf,请安装protobuf-compiler"
fi

# 创建必要目录
echo ""
echo "📁 创建必要目录..."
mkdir -p logs data

# 检查数据库
if [ ! -f yunhu_useralive.db ]; then
    echo "📊 数据库文件不存在,首次运行将自动创建"
fi

# 启动应用
echo ""
echo "🚀 启动应用..."
echo "   Web控制台: http://localhost:5000"
echo "   健康检查: http://localhost:5000/health"
echo "   性能指标: http://localhost:5000/metrics"
echo ""
echo "按 Ctrl+C 停止应用"
echo "=========================================="

# 使用gunicorn启动(生产环境)
if command -v gunicorn &> /dev/null; then
    echo "使用 Gunicorn (生产WSGI服务器)..."
    exec gunicorn \
        --bind 0.0.0.0:5000 \
        --workers 2 \
        --threads 4 \
        --timeout 120 \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log \
        --pid logs/gunicorn.pid \
        app:app
else
    echo "⚠️  Gunicorn 未安装,使用 Flask 开发服务器"
    echo "   生产环境建议安装: pip install gunicorn"
    exec python3 app.py
fi
