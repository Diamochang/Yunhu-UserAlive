# OpenPGP 加密住址使用指南

## 概述

本功能允许您为信任的好友设置点对点的加密住址信息。您需要使用自己的 OpenPGP 密钥对住址进行加密和签名,然后将密文填写在控制台中。当好友需要时,可以通过"住址"关键词触发自动回复。

## 前置要求

1. **安装 GnuPG**: 
   - Linux: `sudo apt-get install gnupg` (Debian/Ubuntu) 或 `sudo dnf install gnupg2` (Fedora)
   - macOS: `brew install gnupg`
   - Windows: 从 https://gnupg.org/download/ 下载

2. **生成或导入您的 OpenPGP 密钥对**

## 步骤 1: 生成 OpenPGP 密钥对(如果没有)

```bash
# 生成交互式密钥
gpg --full-generate-key

# 或者使用默认参数快速生成
gpg --batch --gen-key <<EOF
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: 您的姓名
Name-Email: your-email@example.com
Expire-Date: 0
%commit
EOF
```

## 步骤 2: 导出公钥给好友

```bash
# 列出您的密钥
gpg --list-keys

# 导出公钥(ASCII格式)
gpg --armor --export your-email@example.com > your-public-key.asc

# 将公钥文件发送给您的好友
```

## 步骤 3: 加密住址信息

### 方法 A: 使用命令行

```bash
# 创建包含住址的文本文件
echo "您的详细住址信息" > address.txt

# 使用好友的公钥加密(假设好友的邮箱是 friend@example.com)
gpg --encrypt --recipient friend@example.com --sign address.txt

# 这将生成 address.txt.gpg 文件

# 转换为 Base64 以便复制粘贴
base64 address.txt.gpg > address.txt.gpg.b64

# 查看并复制 Base64 内容
cat address.txt.gpg.b64
```

### 方法 B: 使用 Python 脚本

```python
import subprocess
import base64

def encrypt_address(address_text, recipient_email):
    """使用GPG加密住址"""
    # 创建临时文件
    with open('address.txt', 'w', encoding='utf-8') as f:
        f.write(address_text)
    
    # 加密
    subprocess.run([
        'gpg', '--encrypt',
        '--recipient', recipient_email,
        '--sign',
        'address.txt'
    ])
    
    # 读取加密文件并转为Base64
    with open('address.txt.gpg', 'rb') as f:
        encrypted_data = f.read()
    
    return base64.b64encode(encrypted_data).decode('utf-8')

# 使用示例
address = "北京市朝阳区xxx路xxx号xxx室"
friend_email = "friend@example.com"
encrypted = encrypt_address(address, friend_email)
print("加密后的密文(Base64):")
print(encrypted)
```

## 步骤 4: 在控制台中配置

1. 登录 Web 控制台
2. 进入"设置"页面
3. 在"添加信任好友"部分:
   - **好友云湖ID**: 输入好友的云湖 ID
   - **备注名**: (可选) 好友的备注名
   - **加密住址信息**: 粘贴上一步生成的 Base64 密文
   - **启用局部"电子终别"标记**: 勾选此选项会在回复中添加提醒
4. 点击"添加"

## 步骤 5: 好友如何解密

您的好友收到加密住址后,可以使用他们的私钥解密:

```bash
# 如果收到的是 .gpg 文件
gpg --decrypt address.txt.gpg

# 如果收到的是 Base64 编码
echo "BASE64_CONTENT_HERE" | base64 -d | gpg --decrypt
```

## 电子终别功能

### 全局电子终别
在控制台的"设置"页面可以设置自动开启电子终别的延迟时间。当超过设定时间未访问控制台时,系统会自动启用全局电子终别。

### 局部电子终别
为特定好友启用"电子终别"标记后,当该好友查询住址时,系统会自动附加提醒消息:

```
⚠️【电子终别】特别提醒：请在信封上写明你的名址，以免失去最后的联系。
```

## 安全注意事项

1. **保护私钥**: 永远不要泄露您的私钥
2. **备份密钥**: 定期备份您的 GPG 密钥对
3. **验证指纹**: 与好友交换密钥时,验证密钥指纹以确保真实性
4. **定期更新**: 定期更换密钥以提高安全性

## 常见问题

### Q: 为什么使用 OpenPGP 而不是其他加密方式?
A: OpenPGP 是成熟的端到端加密标准,支持数字签名,确保消息的完整性和不可否认性。

### Q: 我可以为同一个好友存储多个住址吗?
A: 当前版本每个好友只能存储一个加密住址。如需多个,可以在住址文本中包含多条信息。

### Q: 如果忘记解密密码怎么办?
A: OpenPGP 使用密钥对加密,只要私钥存在就可以解密。请务必备份您的私钥和密码短语。

### Q: 加密后的密文很长,有长度限制吗?
A: 数据库字段使用 TEXT 类型,理论上没有严格限制。但建议保持合理长度。

## 技术支持

如有问题,请查看项目文档或提交 Issue。
