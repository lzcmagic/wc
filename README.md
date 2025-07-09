# A股选股网站 - StockSelector

## 项目概述
专业的A股选股分析平台，提供实时数据分析、智能选股策略和投资组合管理功能。

## 技术栈
- **后端**: Python + Flask + AkShare
- **配置管理**: 环境变量 + .env 文件
- **部署**: GitHub Actions + 微信推送通知

## 核心功能
1. 🔍 智能选股系统
2. 📊 数据可视化分析
3. 💼 投资组合管理
4. ⚡ 实时行情推送
5. 📈 策略回测功能
6. 📱 微信推送通知 (WxPusher)

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
cp .env.example .env

# 编辑 .env 文件，配置微信推送
# 微信推送配置
WXPUSHER_ENABLED=true
WXPUSHER_APP_TOKEN=AT_your_token    # WxPusher应用TOKEN
WXPUSHER_TOPIC_IDS=41366           # 推送主题ID
# 或使用极简推送
WXPUSHER_SPT=SPT_your_token        # 极简推送token
```

### 3. 本地测试
```bash
# 测试配置
python -c "from core.env_config import env_config; env_config.print_config_status()"

# 启动Web服务
python web_app.py
```

### 4. GitHub Actions 配置
GitHub Actions已配置为使用硬编码的WxPusher配置，无需额外设置。

详细配置说明请查看 [WxPusher配置指南](WxPusher配置指南.md)

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

配置系统说明：

- **微信推送配置**：使用WxPusher进行微信推送通知
- **策略配置**：选股参数，存储在 `core/strategy_config.py`

详细说明请查看 [WxPusher配置指南](WxPusher配置指南.md)

## 📈 使用方法

### 命令行
```bash
# 执行选股 (自动发送邮件和微信通知)
python main.py select --strategy technical
python main.py select --strategy comprehensive

# 策略回测
python main.py backtest --strategy technical --start 2024-01-01 --end 2024-12-31

# 测试微信推送
python main.py test-wxpusher --config  # 查看配置状态
python main.py test-wxpusher --send    # 发送测试消息
```

### Web界面
```bash
python web_app.py
# 访问 http://localhost:5000
```

## 📱 微信推送配置

本系统集成了WxPusher微信推送功能，可将选股结果直接推送到微信。

### 快速配置 (极简推送)
1. 扫描二维码获取SPT: [点击获取](https://wxpusher.zjiecode.com/api/qrcode/RwjGLMOPTYp35zSYQr0HxbCPrV9eU0wKVBXU1D5VVtya0cQXEJWPjqBdW3gKLifS.jpg)
2. 在 `.env` 文件中配置:
   ```bash
   WXPUSHER_ENABLED=true
   WXPUSHER_SPT=SPT_您的Token
   ```
3. 测试推送: `python main.py test-wxpusher --send`

### 高级配置 (标准推送)
1. 访问 [WxPusher管理后台](https://wxpusher.zjiecode.com/admin/)
2. 创建应用并获取APP_TOKEN
3. 获取用户UID
4. 配置环境变量:
   ```bash
   WXPUSHER_ENABLED=true
   WXPUSHER_APP_TOKEN=AT_您的Token
   WXPUSHER_UIDS=UID_用户1,UID_用户2
   ```

详细配置指南请参考: [WxPusher集成指南](docs/wxpusher_guide.md)

## 法律声明
⚠️ 本平台仅提供数据分析工具，不构成任何投资建议。股市有风险，投资需谨慎。 