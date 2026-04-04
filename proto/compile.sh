#!/bin/bash
# 编译ProtoBuf文件

set -e

echo "编译ProtoBuf文件..."

# 检查protoc是否安装
if ! command -v protoc &> /dev/null; then
    echo "错误: 未找到protoc编译器"
    echo "请安装protobuf-compiler:"
    echo "  Ubuntu/Debian: sudo apt-get install protobuf-compiler"
    echo "  macOS: brew install protobuf"
    exit 1
fi

# 创建输出目录
mkdir -p proto/generated

# 编译proto文件
protoc --python_out=proto/generated --pyi_out=proto/generated proto/yunhu.proto

echo "✓ ProtoBuf文件编译成功"
echo "生成的文件位于: proto/generated/"
