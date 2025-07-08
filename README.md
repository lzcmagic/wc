# A股选股网站 - StockSelector

## 项目概述
专业的A股选股分析平台，提供实时数据分析、智能选股策略和投资组合管理功能。

## 技术栈
- **后端**: Python + Flask + AkShare
- **配置管理**: 环境变量 + .env 文件
- **部署**: GitHub Actions + 邮件通知

## 核心功能
1. 🔍 智能选股系统
2. 📊 数据可视化分析
3. 💼 投资组合管理
4. ⚡ 实时行情推送
5. 📈 策略回测功能

## 🚀 快速开始

### 1. 环境准备
```bash
# 克隆项目
git clone <your-repo>
cd stock-selector

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境
```bash
# 复制环境配置模板
cp env.example .env

# 编辑 .env 文件，填入你的邮箱配置
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USE_TLS=true
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_TO=your_email@gmail.com
```

### 3. 本地测试
```bash
# 测试配置
python -c "from core.env_config import env_config; env_config.print_config_status()"

# 启动Web服务
python web_app.py
```

### 4. GitHub Actions 配置
在 GitHub 仓库设置中添加以下 Secrets：
- `EMAIL_USERNAME`: 发送邮箱地址
- `EMAIL_PASSWORD`: 邮箱应用密码
- `EMAIL_TO`: 接收邮箱地址

详细配置说明请查看 [配置指南](config_guide.md)

## 📋 选股策略

### 技术分析策略
- 市值筛选：> 50亿
- 涨幅限制：< 30%
- 技术指标：MACD、RSI、KDJ等

### 综合分析策略  
- 市值筛选：> 80亿
- 涨幅限制：< 25%
- 四维分析：技术面 + 基本面 + 市场情绪 + 行业分析

## 🔧 配置说明

新的配置系统将环境配置和策略配置分离：

- **环境配置**：邮箱等敏感信息，使用 `.env` 文件或环境变量
- **策略配置**：选股参数，存储在 `core/strategy_config.py`

详细说明请查看 [配置指南](config_guide.md)

## 📈 使用方法

### 命令行
```bash
# 执行选股
python main.py select --strategy technical
python main.py select --strategy comprehensive

# 发送邮件通知
python send_email_notification.py comprehensive
```

### Web界面
```bash
python web_app.py
# 访问 http://localhost:5000
```

## 法律声明
⚠️ 本平台仅提供数据分析工具，不构成任何投资建议。股市有风险，投资需谨慎。 