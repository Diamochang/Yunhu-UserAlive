# ProtoBuf 使用指南

## 概述

本项目使用 Protocol Buffers (ProtoBuf) 进行云湖通信的序列化和反序列化。所有 ProtoBuf 定义都来自云湖活跃开发者用户的[第三方用户 API 文档](https://yh-api.yyyyt.top/)，确保与云湖服务器完全兼容。

**重要提示**: 云湖API对ProtoBuf的支持是混合的:
- ✅ **大多数用户API**: 必须使用 ProtoBuf (如登录、发送消息、心跳等)
- ⚠️ **部分新API**: 可能仅支持 JSON 格式

本项目的序列化器会自动处理这种情况:
1. 优先尝试使用 ProtoBuf
2. 如果 ProtoBuf 失败，自动降级到 JSON
3. 记录哪些消息类型使用了降级

## 文件结构

```
proto/
├── yunhu.proto              # ProtoBuf 定义文件(来自官方API文档)
├── serializer.py            # 序列化/反序列化工具类
├── compile.sh               # 编译脚本
└── generated/               # 编译生成的Python文件
    ├── __init__.py
    └── yunhu_pb2.py
```

## 安装依赖

### 1. 安装 protobuf 编译器

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install protobuf-compiler
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install protobuf-compiler
```

**macOS:**
```bash
brew install protobuf
```

**Windows:**
从 https://github.com/protocolbuffers/protobuf/releases 下载 protoc 编译器

### 2. 安装 Python 包

```bash
pip install protobuf
```

### 3. 编译 ProtoBuf 文件

```bash
cd proto
bash compile.sh
```

这会生成 `proto/generated/yunhu_pb2.py` 文件。

## 支持的 ProtoBuf 消息类型

[yunhu.proto](yunhu.proto) 包含了第三方文档中重要的消息类型，具体如下:

### WebSocket 基础消息
- `WSLogin` - WebSocket 登录
- `WSHeartbeat` - 心跳请求
- `WSHeartbeatAck` - 心跳响应
- `WSLogout` - 退出登录

### 发送消息
- `SendMessageRequest` - 发送消息请求
  - 支持文本、Markdown、HTML
  - 支持引用消息
  - 支持 @用户
  - 支持媒体文件(图片、视频、音频、文件)

### 编辑消息
- `EditMessageRequest` - 编辑消息请求

### 撤回消息
- `RecallMessageRequest` - 撤回单条消息
- `BatchRecallMessageRequest` - 批量撤回消息

### 接收消息
- `PushMessage` - 推送消息(服务端->客户端)
  - 包含完整的消息信息
  - 包含发送者信息
  - 包含内容类型

### 已读消息
- `ReadMessageRequest` - 标记消息已读

### 按钮事件
- `ButtonReportRequest` - 按钮点击事件报告

### 流式消息
- `StreamMessage` - 流式消息(用于AI回复等)

### 笔记同步
- `InputInfo` - 输入状态同步
- `DraftInput` - 草稿同步

### 其他消息
- `FileSendMessage` - 超级文件分享
- `InviteApply` - 邀请申请
- `EditMessagePush` - 编辑消息推送

## 使用示例

### 基本用法

```python
from proto.serializer import serializer

# 检查 ProtoBuf 是否可用
if serializer.is_proto_available:
    print("✓ ProtoBuf 支持已启用")
else:
    print("⚠ 使用 JSON 格式(性能较低)")
```

### 发送登录消息

```python
# 自动选择 ProtoBuf 或 JSON
login_data = serializer.serialize_login(
    user_id="123456",
    token="your-token-here",
    platform="windows",
    device_id="UserAlive"
)

# 发送到 WebSocket
ws.send(login_data)
```

### 发送文本消息

```python
msg_data = serializer.serialize_send_message(
    chat_id="679137839",
    chat_type=2,  # 群聊
    text="Hello, World!",
    content_type=1  # 文本
)

ws.send(msg_data)
```

### 发送 Markdown 消息

```python
msg_data = serializer.serialize_send_message(
    chat_id="123456",
    chat_type=1,  # 私聊
    text="# 标题\n\n这是 **Markdown** 内容",
    content_type=3  # Markdown
)

ws.send(msg_data)
```

### 发送带引用的消息

```python
msg_data = serializer.serialize_send_message(
    chat_id="123456",
    chat_type=1,
    text="回复这条消息",
    content_type=1,
    quote_msg_id="original-msg-id"
)

ws.send(msg_data)
```

### 编辑消息

```python
edit_data = serializer.serialize_edit_message(
    msg_id="msg-to-edit",
    chat_id="123456",
    chat_type=1,
    text="这是修改后的内容",
    content_type=1
)

ws.send(edit_data)
```

### 撤回消息

```python
# 撤回单条消息
recall_data = serializer.serialize_recall_message(
    msg_id="msg-to-recall",
    chat_id="123456",
    chat_type=1
)

ws.send(recall_data)

# 批量撤回
batch_recall_data = serializer.serialize_batch_recall_message(
    msg_ids=["msg1", "msg2", "msg3"],
    chat_id="123456",
    chat_type=1
)

ws.send(batch_recall_data)
```

### 标记消息已读

```python
read_data = serializer.serialize_read_message(
    chat_id="123456",
    chat_type=1,
    last_msg_id="last-read-msg-id"
)

ws.send(read_data)
```

### 按钮事件报告

```python
button_data = serializer.serialize_button_report(
    msg_id="button-msg-id",
    chat_type=1,
    chat_id="123456",
    user_id="user-clicked",
    button_value="button_value_1"
)

ws.send(button_data)
```

### 接收消息

```python
def on_message(ws, message):
    """处理接收到的消息"""
    data = serializer.deserialize_message(message)
    
    if data is None:
        print("无法解析消息")
        return
    
    # 处理推送消息
    if data.get('type') == 'push_message':
        msg = data['msg']
        sender = msg['sender']
        content = msg['content']
        
        print(f"收到来自 {sender['name']} 的消息:")
        print(content['text'])
```

## 降级机制

如果 ProtoBuf 模块未编译或导入失败，序列化器会自动降级到 JSON 格式:

```python
# 首次使用时会尝试导入 ProtoBuf
try:
    from proto.generated import yunhu_pb2
    # 使用 ProtoBuf
except ImportError:
    # 自动降级到 JSON
    logger.warning("ProtoBuf 不可用,使用 JSON 格式")
```

**智能降级策略**:

即使 ProtoBuf 模块可用,某些消息类型也可能因为以下原因失败:
1. ProtoBuf 定义与服务器不匹配
2. 新API尚未添加 ProtoBuf 支持
3. 字段类型不兼容

在这种情况下,序列化器会:
- 记录错误信息(每种消息类型只记录一次)
- 自动降级到 JSON 格式
- 继续正常工作,不影响功能

```python
# 查看哪些消息类型使用了降级
from proto.serializer import serializer

status = serializer.get_status_report()
print(f"ProtoBuf 可用: {status['proto_available']}")
print(f"降级消息数: {status['proto_errors_count']}")
print(f"当前模式: {status['fallback_mode']}")

if status['proto_errors']:
    print("\n降级的消息类型:")
    for msg_type, error in status['proto_errors'].items():
        print(f"  - {msg_type}: {error}")
```

**注意**: 
- JSON 格式功能完全相同,但性能和带宽效率略低于 ProtoBuf
- 对于必须使用 ProtoBuf 的 API，降级可能导致服务器拒绝请求
- 建议定期检查 ProtoBuf 错误日志,确保关键API正常工作

## 性能对比

| 特性 | ProtoBuf | JSON |
|------|----------|------|
| 序列化速度 | 快 (~2x) | 慢 |
| 消息大小 | 小 (~50%) | 大 |
| 可读性 | 二进制 | 文本 |
| 调试难度 | 较难 | 容易 |

## 常见问题

### Q: 为什么需要编译 ProtoBuf?
A: ProtoBuf 需要将 `.proto` 定义文件编译为特定语言的代码才能使用。编译后生成的 Python 代码提供了高效的序列化/反序列化功能。

### Q: 不编译 ProtoBuf 能运行吗?
A: 可以。程序会自动降级到 JSON 格式,功能完全相同,只是性能稍低。

### Q: 如何更新 ProtoBuf 定义?
A: 
1. 从官方 API 文档获取最新的 ProtoBuf 定义
2. 更新 `proto/yunhu.proto` 文件
3. 重新运行 `bash proto/compile.sh`

### Q: ProtoBuf 版本兼容性?
A: 项目使用 ProtoBuf 3 (proto3),确保安装的 `protobuf` Python 包版本 >= 3.0.0。

### Q: 如何查看编译后的消息结构?
A: 编译后的 `yunhu_pb2.py` 文件包含所有消息类的定义。可以使用 Python 交互式环境查看:

```python
from proto.generated import yunhu_pb2
help(yunhu_pb2.SendMessageRequest)
```

## 开发者注意事项

1. **不要手动修改** `proto/generated/yunhu_pb2.py`,它是自动生成的
2. **保持 yunhu.proto 与官方文档同步**,不要做任何修改
3. **添加新消息类型时**,同时在 `serializer.py` 中添加对应的序列化方法
4. **测试时**,建议同时测试 ProtoBuf 和 JSON 两种模式

## 相关资源

- [Protocol Buffers 官方文档](https://developers.google.com/protocol-buffers)
- [云湖 API 文档](https://yh-api.yyyyt.top/api/v1/)
- [ProtoBuf Python 教程](https://developers.google.com/protocol-buffers/docs/pythontutorial)
