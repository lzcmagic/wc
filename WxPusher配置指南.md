# WxPusher微信推送配置指南

## 概述

WxPusher是一个基于微信公众号的实时消息推送平台，可以通过API发送消息到微信，适用于服务器报警、信息更新提示等场景。本项目已集成WxPusher，用于发送每日选股结果推送。

## 配置步骤

### 1. 注册WxPusher账号

1. 访问 [WxPusher官网](https://wxpusher.zjiecode.com/)
2. 点击"免费注册"创建账号
3. 登录后进入管理后台

### 2. 创建应用

1. 在管理后台点击"应用管理" → "新建应用"
2. 填写应用信息：
   - 应用名称：A股智能选股系统
   - 应用类型：选择合适的类型
   - 应用描述：每日选股结果推送
3. 创建成功后，记录下 **APP_TOKEN**（格式：AT_xxxxxxxxx）

### 3. 获取推送目标

#### 方式一：主题推送（推荐）
1. 在应用管理中点击"主题管理"
2. 创建新主题，记录下 **主题ID**（数字）
3. 将主题二维码分享给需要接收推送的用户
4. 用户扫码关注后即可接收推送

#### 方式二：用户UID推送
1. 用户关注您的应用后
2. 在"用户管理"中查看用户的 **UID**（格式：UID_xxxxxxxxx）
3. 记录需要推送的用户UID

### 4. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# WxPusher微信推送配置
WXPUSHER_ENABLED=true
WXPUSHER_APP_TOKEN=AT_your_app_token_here

# 推送方式选择其一：

# 方式一：主题推送（推荐）
WXPUSHER_TOPIC_IDS=41366

# 方式二：用户UID推送
WXPUSHER_UIDS=UID_xxxxxxxxx,UID_yyyyyyyyy

# 方式三：极简推送（无需创建应用）
WXPUSHER_SPT=SPT_your_simple_token_here
```

### 5. GitHub Actions配置

如果使用GitHub Actions自动化，无需额外配置。WxPusher配置已硬编码在代码中：
- APP_TOKEN: `AT_fWXnH05M1MD8wFunlBRioiFtW5JL5yGm`
- TOPIC_ID: `41366`

## 测试推送功能

### 本地测试

```bash
# 测试WxPusher配置和发送
python main.py test-wxpusher --send

# 仅查看配置状态
python main.py test-wxpusher --config
```

### GitHub Actions测试

1. 在GitHub仓库的Actions页面
2. 手动触发"测试微信推送"工作流
3. 查看执行日志确认推送是否成功

## 推送内容

系统会发送包含以下信息的微信推送：

- 📈 选股策略名称
- 📅 选股日期
- 📊 选中股票列表（代码、名称、得分、价格等）
- 💡 推荐理由
- ⚠️ 风险提示

## 常见问题

### Q: 推送失败怎么办？
A: 检查以下几点：
1. APP_TOKEN是否正确
2. 主题ID或用户UID是否有效
3. 网络连接是否正常
4. WxPusher服务是否正常

### Q: 如何切换推送方式？
A: 修改 `.env` 文件中的配置：
- 主题推送：设置 `WXPUSHER_TOPIC_IDS`
- 用户推送：设置 `WXPUSHER_UIDS`
- 极简推送：设置 `WXPUSHER_SPT`

### Q: 极简推送和标准推送有什么区别？
A: 
- 标准推送：需要创建应用，支持更多功能
- 极简推送：无需创建应用，配置简单，但功能有限

## 相关链接

- [WxPusher官网](https://wxpusher.zjiecode.com/)
- [WxPusher API文档](https://wxpusher.zjiecode.com/docs/)
- [WxPusher管理后台](https://wxpusher.zjiecode.com/admin/)

## 注意事项

1. 请妥善保管APP_TOKEN，避免泄露
2. 推送频率不要过高，避免被限制
3. 推送内容请遵守相关法律法规
4. 建议定期检查推送功能是否正常
