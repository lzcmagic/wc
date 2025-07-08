# 配置系统使用指南

## 🎯 配置系统概述

新的配置系统将环境配置和策略配置完全分离：

- **环境配置**：SMTP邮箱等敏感信息，支持`.env`文件和环境变量
- **策略配置**：选股参数和业务逻辑，存储在代码中，两个环境共享

## 📁 配置文件结构

```
项目根目录/
├── .env                    # 本地环境配置（不提交到git）
├── env.example             # 环境配置模板
├── core/
│   ├── env_config.py       # 环境配置管理
│   ├── strategy_config.py  # 策略配置管理
│   └── config.py           # 统一配置入口
└── README.md
```

## 🏠 本地开发配置

### 1. 创建 `.env` 文件

```bash
# 复制模板文件
cp env.example .env
```

### 2. 编辑 `.env` 文件

```bash
# 邮件配置环境变量
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=your_email@gmail.com
EMAIL_SUBJECT_TEMPLATE=📈 每日选股推荐 - {date}
```

### 3. 安装依赖

```bash
pip install python-dotenv
# 或者
pip install -r requirements.txt
```

### 4. 运行测试

```bash
python -c "
from core.env_config import env_config
env_config.print_config_status()
"
```

## ☁️ GitHub Actions 配置

### 1. 设置 GitHub Secrets

在 GitHub 仓库设置中添加以下 Secrets：

| Secret 名称 | 说明 | 示例 |
|------------|------|------|
| `EMAIL_ENABLED` | 是否启用邮件 | `true` |
| `EMAIL_SMTP_SERVER` | SMTP服务器 | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP端口 | `587` |
| `EMAIL_USE_TLS` | 是否使用TLS | `true` |
| `EMAIL_USERNAME` | 发送邮箱 | `your_email@gmail.com` |
| `EMAIL_PASSWORD` | 邮箱密码 | `your_app_password` |
| `EMAIL_TO` | 接收邮箱 | `your_email@gmail.com` |

### 2. GitHub Actions 自动使用

系统会自动从环境变量读取配置，无需额外配置。

## 🎛️ 策略配置

策略配置存储在 `core/strategy_config.py` 中，包含：

### 技术分析策略
```python
TECHNICAL_STRATEGY = {
    'min_market_cap': 5000000000,  # 50亿
    'max_recent_gain': 30,         # 30%
    'min_score': 60,               # 最低评分
    'max_stocks': 10,              # 最多推荐数量
    # ... 更多配置
}
```

### 综合分析策略
```python
COMPREHENSIVE_STRATEGY = {
    'min_market_cap': 8000000000,  # 80亿
    'max_recent_gain': 25,         # 25%
    'min_score': 75,               # 最低评分
    'max_stocks': 8,               # 最多推荐数量
    # ... 更多配置
}
```

## 🔧 配置管理

### 获取邮件配置
```python
from core.env_config import env_config

email_config = env_config.get_email_config()
print(f"邮件启用状态: {email_config['enabled']}")
```

### 获取策略配置
```python
from core.strategy_config import strategy_config

technical_config = strategy_config.get_strategy_config('technical')
print(f"技术策略最小市值: {technical_config['min_market_cap']}")
```

### 验证配置
```python
from core.env_config import env_config
from core.strategy_config import strategy_config

# 验证邮件配置
env_config.validate_email_config()

# 验证策略配置
strategy_config.validate_strategy_config('technical')
```

## 🚀 快速启动

### 本地测试
```bash
# 1. 配置环境
cp env.example .env
# 编辑 .env 文件

# 2. 安装依赖
pip install -r requirements.txt

# 3. 测试配置
python -c "from core.config import config"

# 4. 启动应用
python web_app.py
```

### GitHub Actions
```bash
# 1. 设置 GitHub Secrets
# 2. 推送代码
git push origin main

# 3. 触发工作流
# 在 GitHub Actions 页面手动触发
```

## ❓ 常见问题

### Q: 本地提示"未找到 .env 文件"
A: 
```bash
cp env.example .env
# 然后编辑 .env 文件填入真实配置
```

### Q: GitHub Actions 邮件发送失败
A: 检查 GitHub Secrets 是否正确设置，特别是：
- 邮箱地址格式
- 应用密码（不是登录密码）
- SMTP 服务器和端口

### Q: 如何修改策略参数
A: 直接编辑 `core/strategy_config.py` 文件，修改对应策略的配置。

### Q: 如何添加新的环境变量
A: 
1. 在 `env.example` 中添加变量
2. 在 `core/env_config.py` 中添加读取逻辑
3. 在 GitHub Secrets 中设置对应值

## 🔒 安全说明

- `.env` 文件包含敏感信息，已添加到 `.gitignore`
- GitHub Secrets 安全存储，不会在日志中显示
- 邮箱应用密码比登录密码更安全
- 定期更换邮箱应用密码

## 📝 配置模板

### Gmail 配置
```bash
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
```

### QQ邮箱配置
```bash
EMAIL_SMTP_SERVER=smtp.qq.com
EMAIL_SMTP_PORT=465
EMAIL_USE_TLS=false
```

### 163邮箱配置
```bash
EMAIL_SMTP_SERVER=smtp.163.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
``` 