# ProtoBuf 混合支持优化说明

## 背景

云湖API对ProtoBuf的支持是**混合的**:
- ✅ **大多数用户API**: 必须使用 ProtoBuf (登录、发送消息、心跳等核心功能)
- ⚠️ **部分新API**: 可能仅支持 JSON 格式

这种混合支持要求我们的序列化器具备智能降级能力。

## 优化内容

### 1. 智能降级策略

#### 之前的问题
- ProtoBuf失败时只记录错误日志
- 无法追踪哪些消息类型使用了降级
- 用户不知道当前使用的是ProtoBuf还是JSON

#### 优化后的方案
```python
class ProtoBufSerializer:
    def __init__(self):
        self._proto_errors = {}  # 记录哪些消息类型ProtoBuf失败
    
    def serialize_xxx(self, ...):
        if self._use_proto:
            try:
                # 尝试ProtoBuf序列化
                return proto_msg.SerializeToString()
            except Exception as e:
                error_key = "MessageTypeName"
                if error_key not in self._proto_errors:
                    # 每种消息类型只记录一次错误
                    self._proto_errors[error_key] = str(e)
                    logger.warning(f"⚠ ProtoBuf序列化失败 [{error_key}],回退到JSON: {e}")
        
        # 降级到JSON
        return json.dumps(message).encode('utf-8')
```

**优势**:
- ✅ 自动处理混合支持情况
- ✅ 每种消息类型只记录一次错误(避免日志 spam)
- ✅ 不影响功能,无缝降级
- ✅ 可追踪哪些API需要修复

### 2. 状态监控API

新增方法用于监控ProtoBuf状态:

```python
# 获取ProtoBuf错误统计
errors = serializer.get_proto_errors()
# 返回: {"WSLogin": "field 'xyz' not found", ...}

# 获取完整状态报告
status = serializer.get_status_report()
# 返回:
{
    "proto_available": True,
    "proto_errors_count": 2,
    "proto_errors": {
        "NewAPI1": "message type not found",
        "NewAPI2": "incompatible field type"
    },
    "fallback_mode": "JSON"  # 或 "ProtoBuf"
}

# 清除错误记录(用于重新测试)
serializer.clear_proto_errors()
```

### 3. WebSocket客户端集成

在 `websocket_client.py` 中添加ProtoBuf状态:

```python
def get_stats(self) -> Dict[str, Any]:
    stats = self.stats.copy()
    
    # 添加 ProtoBuf 状态
    from proto.serializer import serializer
    stats["proto_support"] = serializer.is_proto_available
    stats["proto_status"] = serializer.get_status_report()
    stats["platform"] = self.platform
    
    return stats
```

### 4. Web控制台显示

#### API端点增强
`/api/status` 现在返回ProtoBuf状态:

```json
{
    "websocket_connected": true,
    "scheduler_running": true,
    "timestamp": "2024-04-05T12:00:00",
    "proto": {
        "proto_available": true,
        "proto_errors_count": 1,
        "proto_errors": {
            "SomeNewAPI": "message type not defined"
        },
        "fallback_mode": "JSON"
    }
}
```

#### 仪表板显示
在Web控制台的"运行状态"卡片中显示:

```
运行状态
├─ WebSocket: 在线 🟢
├─ 定时任务: 运行中 🟢
├─ ProtoBuf: JSON (1个降级) 🔴
└─ 最后签到: 2024-04-05 00:00:00
```

**状态指示**:
- 🟢 `ProtoBuf (正常)` - 所有消息都使用ProtoBuf
- 🔴 `JSON (N个降级)` - 有N个消息类型降级到JSON
- 🔴 `JSON (降级模式)` - ProtoBuf模块未加载

### 5. 日志优化

#### 启动时日志
```
✓ ProtoBuf支持已启用
  提示: 大多数云湖API需要ProtoBuf,部分新API使用JSON
```

或

```
⚠ ProtoBuf模块未找到,将使用JSON格式: No module named 'proto.generated'
  重要: 某些云湖API可能需要ProtoBuf才能正常工作
  建议运行: bash proto/compile.sh 启用ProtoBuf支持
```

#### 运行时警告
```
⚠ ProtoBuf序列化失败 [NewAPI],回退到JSON: message type not found
```

**注意**: 每种消息类型只在第一次失败时记录,避免重复日志。

## 使用场景

### 场景1: 全新安装(无ProtoBuf)

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动程序(自动使用JSON)
python app.py

# 日志输出:
# ⚠ ProtoBuf模块未找到,将使用JSON格式
#   重要: 某些云湖API可能需要ProtoBuf才能正常工作
#   建议运行: bash proto/compile.sh 启用ProtoBuf支持

# 3. (可选) 编译ProtoBuf获得更好性能
cd proto && bash compile.sh && cd ..
```

### 场景2: 部分API降级

```python
from proto.serializer import serializer

# 检查状态
status = serializer.get_status_report()
print(f"当前模式: {status['fallback_mode']}")
print(f"降级数量: {status['proto_errors_count']}")

if status['proto_errors']:
    print("\n需要修复的消息类型:")
    for msg_type, error in status['proto_errors'].items():
        print(f"  - {msg_type}: {error}")
        print(f"    建议: 检查 yunhu.proto 是否包含此消息定义")
```

### 场景3: 调试ProtoBuf问题

```python
from proto.serializer import serializer

# 1. 清除之前的错误记录
serializer.clear_proto_errors()

# 2. 执行操作触发序列化
ws_client.send_text_message("123", 1, "test")

# 3. 检查是否有新的错误
errors = serializer.get_proto_errors()
if errors:
    print("发现ProtoBuf错误:")
    for msg_type, error in errors.items():
        print(f"{msg_type}: {error}")
else:
    print("✓ 所有消息都成功使用ProtoBuf")
```

## 最佳实践

### 1. 生产环境建议

✅ **推荐**: 编译并启用ProtoBuf
- 更好的性能(~2x 序列化速度)
- 更小的消息体积(~50%)
- 兼容所有云湖API

❌ **不推荐**: 仅使用JSON
- 某些API可能拒绝JSON请求
- 性能和带宽效率较低
- 仅适用于测试环境

### 2. 监控建议

定期检查ProtoBuf状态:

```python
# 添加到健康检查端点
@app.route('/health')
def health_check():
    from proto.serializer import serializer
    
    status = serializer.get_status_report()
    
    health = {
        "status": "healthy",
        "proto": {
            "available": status["proto_available"],
            "mode": status["fallback_mode"],
            "errors": status["proto_errors_count"]
        }
    }
    
    # 如果有太多降级,标记为degraded
    if status["proto_errors_count"] > 5:
        health["status"] = "degraded"
        health["warning"] = "多个消息类型降级到JSON,建议检查ProtoBuf定义"
    
    return jsonify(health)
```

### 3. 开发建议

添加新API时:

1. **首先检查** `yunhu.proto` 是否有对应的消息定义
2. **如果没有**,从官方API文档获取ProtoBuf定义
3. **更新** `proto/yunhu.proto`
4. **重新编译** `bash proto/compile.sh`
5. **在** `serializer.py` **中添加序列化方法**
6. **测试** 确保ProtoBuf正常工作

## 常见问题

### Q: 为什么有些API会降级到JSON?

A: 可能的原因:
1. ProtoBuf定义与服务器版本不匹配
2. 新API尚未添加到 `yunhu.proto`
3. 字段类型或名称不一致
4. ProtoBuf编译器版本过旧

### Q: 降级会影响功能吗?

A: 
- **大多数情况**: 不会影响,JSON和ProtoBuf功能相同
- **少数情况**: 某些API可能拒绝JSON请求,导致功能失效
- **建议**: 定期检查错误日志,确保关键API正常工作

### Q: 如何知道哪些API必须使用ProtoBuf?

A: 
1. 查看云湖官方API文档
2. 观察日志中的错误信息
3. 如果某个API在JSON模式下失败,很可能需要ProtoBuf
4. 核心API(登录、发送消息、心跳)通常必须使用ProtoBuf

### Q: 可以强制使用ProtoBuf吗?

A: 当前设计是自动降级,不建议强制。如果某个API必须使用ProtoBuf:

```python
def send_critical_message(...):
    """发送关键消息(必须使用ProtoBuf)"""
    from proto.serializer import serializer
    
    if not serializer.is_proto_available:
        raise RuntimeError("此操作需要ProtoBuf支持,请编译ProtoBuf文件")
    
    # 发送消息
    ...
```

### Q: 如何清除错误记录?

A: 
```python
from proto.serializer import serializer

# 清除所有错误记录
serializer.clear_proto_errors()

# 或在Web控制台中刷新页面(每5秒自动更新状态)
```

## 技术细节

### 错误去重机制

```python
# 每种消息类型只记录一次错误
error_key = "MessageTypeName"
if error_key not in self._proto_errors:
    self._proto_errors[error_key] = str(e)
    logger.warning(f"⚠ ProtoBuf序列化失败 [{error_key}],回退到JSON: {e}")
# 后续同样的错误不会再次记录
```

### 状态判断逻辑

```python
def get_status_report(self) -> dict:
    return {
        "proto_available": self._use_proto,
        "proto_errors_count": len(self._proto_errors),
        "proto_errors": self._proto_errors.copy(),
        # 判断当前模式
        "fallback_mode": "JSON" if not self._use_proto or self._proto_errors else "ProtoBuf"
    }
```

**判断规则**:
- 如果ProtoBuf模块不可用 → JSON
- 如果有任何消息类型降级 → JSON
- 否则 → ProtoBuf

## 总结

通过智能降级策略和完善的监控机制,我们实现了:

✅ **兼容性**: 同时支持ProtoBuf和JSON
✅ **可靠性**: 自动降级,不影响功能
✅ **可观测性**: 实时监控ProtoBuf状态
✅ **可维护性**: 清晰的错误记录和诊断信息

这确保了项目能够适应云湖API的混合支持情况,同时为用户提供清晰的状态反馈。
