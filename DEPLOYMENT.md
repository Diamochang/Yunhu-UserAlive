# 生产环境部署指南

## 目录
- [快速开始](#快速开始)
- [Docker部署(推荐)](#docker部署推荐)
- [传统部署](#传统部署)
- [Systemd服务部署](#systemd服务部署)
- [Nginx反向代理](#nginx反向代理)
- [监控和维护](#监控和维护)

---

## 快速开始

### 前置要求
- Python 3.9+
- pip
- (可选) Docker & Docker Compose
- (可选) Nginx
- (可选) protoc (ProtoBuf编译器)

### 1. 克隆项目
```bash
git clone <repository-url>
cd Yunhu-UserAlive
```

### 2. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件,设置必要的环境变量
nano .env
```

**必须设置的变量:**
- `MASTER_PASSWORD`: 主密码(至少8位)
- `FLASK_SECRET_KEY`: Flask密钥(随机字符串)
- `ENCRYPTION_SALT`: 加密盐值(随机字符串)

### 3. 启动应用

**方式一: 使用启动脚本(推荐)**
```bash
chmod +x start.sh
./start.sh
```

**方式二: Docker Compose(推荐用于生产)**
```bash
docker-compose up -d
```

**方式三: 手动启动**
```bash
pip install -r requirements.txt
python app.py
```

---

## Docker部署(推荐)

### 优势
- ✅ 环境隔离
- ✅ 易于部署和升级
- ✅ 自动健康检查
- ✅ 资源限制

### 步骤

1. **构建镜像**
```bash
docker-compose build
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **查看日志**
```bash
docker-compose logs -f
```

4. **停止服务**
```bash
docker-compose down
```

5. **更新应用**
```bash
git pull
docker-compose build
docker-compose up -d
```

### 数据持久化
Docker Compose已配置以下卷挂载:
- `./data` - 数据库文件
- `./logs` - 日志文件
- `.env` - 环境变量

---

## 传统部署

### 1. 安装依赖
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python包
pip install -r requirements.txt
```

### 2. 编译ProtoBuf(可选)
```bash
# Ubuntu/Debian
sudo apt-get install protobuf-compiler

# macOS
brew install protobuf

# 编译
bash proto/compile.sh
```

### 3. 配置环境变量
```bash
cp .env.example .env
nano .env
```

### 4. 启动应用
```bash
# 开发环境
python app.py

# 生产环境(使用Gunicorn)
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 app:app
```

---

## Systemd服务部署

适用于Linux服务器,实现开机自启和自动重启。

### 1. 创建系统用户
```bash
sudo useradd -r -s /bin/false yunhu
```

### 2. 部署应用
```bash
sudo mkdir -p /opt/yunhu-useralive
sudo cp -r * /opt/yunhu-useralive/
sudo chown -R yunhu:yunhu /opt/yunhu-useralive
```

### 3. 创建虚拟环境
```bash
cd /opt/yunhu-useralive
sudo -u yunhu python3 -m venv venv
sudo -u yunhu venv/bin/pip install -r requirements.txt
```

### 4. 安装systemd服务
```bash
sudo cp deploy/yunhu-useralive.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable yunhu-useralive
sudo systemctl start yunhu-useralive
```

### 5. 管理服务
```bash
# 查看状态
sudo systemctl status yunhu-useralive

# 查看日志
sudo journalctl -u yunhu-useralive -f

# 重启服务
sudo systemctl restart yunhu-useralive

# 停止服务
sudo systemctl stop yunhu-useralive
```

---

## Nginx反向代理

### 1. 安装Nginx
```bash
# Ubuntu/Debian
sudo apt-get install nginx

# CentOS/RHEL
sudo yum install nginx
```

### 2. 配置Nginx
```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/yunhu-useralive
sudo ln -s /etc/nginx/sites-available/yunhu-useralive /etc/nginx/sites-enabled/
```

### 3. 修改配置
编辑 `/etc/nginx/sites-available/yunhu-useralive`:
- 修改 `server_name` 为你的域名
- 配置SSL证书路径(使用Let's Encrypt)

### 4. 获取SSL证书
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yunhu.example.com
```

### 5. 测试并重启
```bash
sudo nginx -t
sudo systemctl restart nginx
```

---

## 监控和维护

### 健康检查
```bash
curl http://localhost:5000/health
```

响应示例:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-05T12:00:00",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "websocket": "connected",
    "scheduler": "running"
  }
}
```

### Prometheus指标
```bash
curl http://localhost:5000/metrics
```

### 日志查看

**Docker:**
```bash
docker-compose logs -f
```

**Systemd:**
```bash
sudo journalctl -u yunhu-useralive -f
```

**文件日志:**
```bash
tail -f logs/app.log
tail -f logs/app_error.log
```

### 数据库备份
```bash
# 备份
cp yunhu_useralive.db backup_$(date +%Y%m%d_%H%M%S).db

# 恢复
cp backup_20260405_120000.db yunhu_useralive.db
```

### 性能调优

**Gunicorn参数调整:**
```bash
# 根据CPU核心数调整worker数量
# 公式: workers = (2 x CPU cores) + 1
gunicorn --workers 5 --threads 4 app:app
```

**数据库优化:**
- 定期清理旧日志
- 启用WAL模式: `PRAGMA journal_mode=WAL;`
- 定期VACUUM: `VACUUM;`

---

## 故障排除

### 常见问题

**1. 端口被占用**
```bash
# 查找占用端口的进程
lsof -i :5000
# 或更改端口
gunicorn --bind 0.0.0.0:8080 app:app
```

**2. 权限问题**
```bash
# 确保目录权限正确
chown -R yunhu:yunhu /opt/yunhu-useralive
chmod 755 /opt/yunhu-useralive
```

**3. 数据库锁定**
```bash
# 检查是否有其他进程使用数据库
lsof yunhu_useralive.db
# 删除锁文件
rm yunhu_useralive.db-shm yunhu_useralive.db-wal
```

**4. WebSocket连接失败**
- 检查防火墙设置
- 确认云湖API可访问
- 查看日志中的错误信息

### 获取帮助

1. 查看日志文件
2. 检查健康检查端点
3. 查阅GitHub Issues
4. 联系技术支持

---

## 安全建议

1. **使用强密码**: MASTER_PASSWORD至少16位
2. **启用HTTPS**: 始终使用SSL/TLS
3. **防火墙配置**: 只开放必要端口
4. **定期更新**: 保持系统和依赖最新
5. **备份策略**: 定期备份数据库
6. **监控告警**: 设置异常告警
7. **访问控制**: 限制管理界面访问IP

---

## 升级指南

### 小版本升级
```bash
git pull
pip install -r requirements.txt
sudo systemctl restart yunhu-useralive
```

### 大版本升级
1. 备份数据库
2. 阅读CHANGELOG
3. 测试新版本的兼容性
4. 在测试环境验证
5. 生产环境升级

---

**祝部署顺利! 🎉**
