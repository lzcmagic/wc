# WxPusher微信推送集成指南

## 📱 功能介绍

WxPusher是一个使用微信公众号作为通道的实时信息推送平台。本系统已集成WxPusher，可以将选股结果直接推送到您的微信，无需安装额外软件。

## 🎯 推送效果

- **选股结果通知**: 每日选股完成后自动推送
- **富文本消息**: 支持HTML格式，显示股票信息、价格、涨跌幅等
- **实时推送**: 选股完成后立即推送到微信
- **多用户支持**: 可同时推送给多个用户

## 🚀 快速开始

### 方式一：极简推送（推荐个人用户）

**适用场景**: 只给自己发消息，配置简单

1. **获取SPT Token**
   - 扫描二维码: https://wxpusher.zjiecode.com/api/qrcode/RwjGLMOPTYp35zSYQr0HxbCPrV9eU0wKVBXU1D5VVtya0cQXEJWPjqBdW3gKLifS.jpg
   - 获取您的SPT Token

2. **配置环境变量**
   ```bash
   # 在 .env 文件中添加
   WXPUSHER_ENABLED=true
   WXPUSHER_SPT=SPT_您的Token
   ```

3. **测试推送**
   ```bash
   python main.py test-wxpusher --send
   ```

### 方式二：标准推送（推荐多用户）

**适用场景**: 推送给多个用户，功能完整

1. **创建应用**
   - 访问: https://wxpusher.zjiecode.com/admin/
   - 微信扫码登录
   - 点击"创建应用"
   - 填写应用信息并保存

2. **获取APP_TOKEN**
   - 在应用管理页面复制APP_TOKEN

3. **获取用户UID**
   
   **方法一: 用户自助获取**
   - 用户关注公众号"wxpusher"
   - 点击菜单"我的" → "我的UID"
   
   **方法二: 扫码关注获取**
   - 用户扫描您应用的二维码
   - 系统自动获取UID（需配置回调）

4. **配置环境变量**
   ```bash
   # 在 .env 文件中添加
   WXPUSHER_ENABLED=true
   WXPUSHER_APP_TOKEN=AT_您的Token
   WXPUSHER_UIDS=UID_用户1,UID_用户2
   ```

5. **测试推送**
   ```bash
   python main.py test-wxpusher --send
   ```

## ⚙️ 配置详解

### 环境变量说明

```bash
# 基础配置
WXPUSHER_ENABLED=true                    # 是否启用WxPusher
WXPUSHER_APP_TOKEN=AT_xxx               # 应用TOKEN（标准推送）
WXPUSHER_SPT=SPT_xxx                    # 极简推送TOKEN

# 推送目标（至少配置一个）
WXPUSHER_UIDS=UID_xxx,UID_yyy          # 用户UID列表
WXPUSHER_TOPIC_IDS=123,456              # 主题ID列表（群发）
```

### 推送目标类型

| 类型 | 配置变量 | 说明 | 适用场景 |
|------|----------|------|----------|
| 用户UID | WXPUSHER_UIDS | 一对一推送 | 个人用户、VIP用户 |
| 主题ID | WXPUSHER_TOPIC_IDS | 群发推送 | 公开订阅、免费用户 |

## 🧪 测试功能

### 查看配置状态
```bash
python main.py test-wxpusher --config
```

### 发送测试消息
```bash
python main.py test-wxpusher --send
```

### 同时查看配置和发送测试
```bash
python main.py test-wxpusher --config --send
```

## 📊 消息格式

### 选股结果消息示例

```
🎯 技术分析策略选股结果
📅 日期: 2024-01-15
📊 选中股票: 8 只
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 贵州茅台 (600519)
   💰 1680.50元 +2.35%
   ⭐ 85.2分

2. 五粮液 (000858)
   💰 158.20元 +1.80%
   ⭐ 82.7分

... 还有 6 只股票
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ 本信息仅供参考，不构成投资建议
🤖 由A股智能选股系统自动生成
```

## 🔧 高级功能

### 主题订阅

1. **创建主题**
   - 在WxPusher管理后台创建主题
   - 获取主题ID

2. **用户订阅**
   - 用户扫描主题二维码订阅
   - 系统群发消息给所有订阅者

3. **配置推送**
   ```bash
   WXPUSHER_TOPIC_IDS=123,456
   ```

### 付费订阅（可选）

WxPusher支持付费订阅功能，可以：
- 区分付费/免费用户
- 设置不同的推送内容
- 管理订阅到期时间

## 📋 常见问题

### Q: 为什么收不到推送消息？

A: 请检查以下几点：
1. 确认 `WXPUSHER_ENABLED=true`
2. 检查TOKEN是否正确
3. 确认UID或主题ID配置正确
4. 运行测试命令验证配置

### Q: 极简推送和标准推送有什么区别？

A: 
- **极简推送**: 简单快速，只能给自己发消息，无需创建应用
- **标准推送**: 功能完整，可管理多个用户，支持主题群发

### Q: 如何获取用户的UID？

A: 有三种方式：
1. 用户关注公众号"wxpusher"查看
2. 用户扫描应用二维码（需配置回调）
3. 使用参数二维码接口

### Q: 推送失败怎么办？

A: 
1. 检查网络连接
2. 验证TOKEN有效性
3. 确认用户UID正确
4. 查看错误日志

## 🔗 相关链接

- [WxPusher官网](https://wxpusher.zjiecode.com/)
- [WxPusher管理后台](https://wxpusher.zjiecode.com/admin/)
- [WxPusher API文档](https://wxpusher.zjiecode.com/docs/)
- [获取极简推送SPT](https://wxpusher.zjiecode.com/api/qrcode/RwjGLMOPTYp35zSYQr0HxbCPrV9eU0wKVBXU1D5VVtya0cQXEJWPjqBdW3gKLifS.jpg)

## 💡 最佳实践

1. **个人使用**: 推荐极简推送，配置简单
2. **多用户**: 推荐标准推送，功能完整
3. **测试先行**: 配置完成后先发送测试消息
4. **备份配置**: 妥善保管TOKEN，避免泄露
5. **监控推送**: 定期检查推送状态和用户反馈
