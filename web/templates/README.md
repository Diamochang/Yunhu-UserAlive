# Web 模板目录

本目录包含 Yunhu-UserAlive 项目的 Flask 模板文件。

## 目录结构

```
templates/
├── base.html          # 基础布局模板(导航栏、页脚等)
├── login.html         # 登录页面
├── dashboard.html     # 仪表板页面
└── settings.html      # 设置页面
```

## 模板说明

### base.html
基础布局模板,所有其他模板都继承自此模板。包含:
- Bootstrap 5 CSS 和 JS
- Bootstrap Icons 图标库
- 响应式导航栏
- 页脚信息
- 通用样式定义

### login.html
用户登录页面,提供:
- 邮箱和密码输入框
- 错误提示显示
- 响应式卡片布局

### dashboard.html
主仪表板页面,显示:
- 用户基本信息
- WebSocket 连接状态
- 定时任务运行状态
- ProtoBuf 支持状态
- 最后签到时间
- 快捷操作按钮
- 使用提示信息

### settings.html
系统设置页面,包含:
- **自动托管设置**
  - 启用/禁用开关
  - 开始/结束时间配置 (YYYY/MM/DD HH:MM:SS)
  - 按星期选择托管日期
  
- **电子终别设置**
  - 延迟发送时间配置
  - 全局标记开关
  
- **文章链接管理**
  - 添加新文章
  - 查看已添加文章列表
  - 删除文章
  
- **好友管理**
  - 添加信任好友
  - 配置 OpenPGP 加密住址
  - 局部电子终别标记
  - 查看好友列表
  - 删除好友

## 技术栈

- **Flask**: Python Web 框架
- **Bootstrap 5.3**: 前端 UI 框架
- **Bootstrap Icons 1.10**: 图标库
- **Jinja2**: Flask 默认模板引擎

## 自定义样式

如需修改样式,可以在 `base.html` 的 `<style>` 标签中添加自定义 CSS,或创建独立的 CSS 文件放在 `web/static/css/` 目录中。

## JavaScript

每个模板可以通过 `{% block extra_js %}` 块添加页面特定的 JavaScript 代码。

## 响应式设计

所有模板都使用 Bootstrap 的栅格系统,支持:
- 桌面端 (>768px): 多列布局
- 平板端 (≥768px): 自适应布局
- 手机端 (<768px): 单列堆叠布局

## 更新日志

### v1.1.0 (2026-04-05)
- ✅ 使用 Bootstrap 5 重构所有模板
- ✅ 将模板从内联字符串迁移到独立文件
- ✅ 添加响应式设计支持
- ✅ 优化移动端用户体验
- ✅ 添加 Bootstrap Icons 图标
- ✅ 改进表单验证和用户反馈
