# 个人每日A股选股系统

## 🎯 系统目标
为个人投资者提供基于流行技术指标的每日自动选股服务，无需复杂配置，一键获取优质股票推荐。

## 📊 核心选股指标

### 1. 技术指标组合
```python
# 主流技术指标权重配置
INDICATORS_WEIGHT = {
    'macd': 0.25,      # MACD金叉/死叉
    'rsi': 0.20,       # RSI超买超卖
    'kdj': 0.20,       # KDJ金叉
    'bollinger': 0.15, # 布林带位置
    'volume': 0.10,    # 成交量放大
    'ma': 0.10        # 均线多头排列
}
```

### 2. 选股条件
- **MACD**: DIF上穿DEA，出现金叉信号
- **RSI**: 30-70区间，避免超买超卖
- **KDJ**: K值上穿D值，J值<80
- **布林带**: 股价接近下轨反弹或突破中轨
- **成交量**: 近3日成交量放大1.5倍以上
- **均线**: 5日线>10日线>20日线，多头排列

### 3. 过滤条件
- 流通市值 > 50亿（避免小盘股操纵）
- 近30日涨幅 < 30%（避免追高）
- 非ST股票，非退市风险股
- 近期无重大利空消息

## 🔧 技术实现方案

### 1. 简化架构
```
数据获取 → 指标计算 → 选股评分 → 结果输出 → 推送通知
    ↓         ↓         ↓         ↓         ↓
  AkShare   TA-Lib   自定义算法   Web展示   邮件/微信
```

### 2. 技术栈选择
- **数据源**: AkShare (免费A股数据)
- **计算库**: pandas + TA-Lib (技术指标)
- **Web框架**: Flask (轻量级)
- **前端**: Bootstrap + ECharts (简单易用)
- **部署**: 本地运行或云服务器

### 3. 核心代码结构
```python
personal_stock_selector/
├── main.py              # 主程序入口
├── data_fetcher.py      # 数据获取模块
├── indicators.py        # 技术指标计算
├── stock_selector.py    # 选股策略
├── web_app.py          # Web界面
├── notifier.py         # 通知模块
├── config.py           # 配置文件
└── templates/          # 网页模板
    └── dashboard.html
```

## 📈 选股策略详解

### 1. 多指标评分系统
```python
def calculate_stock_score(stock_data):
    score = 0
    
    # MACD评分 (0-25分)
    if macd_golden_cross(stock_data):
        score += 25
    elif macd_above_zero(stock_data):
        score += 15
    
    # RSI评分 (0-20分)
    rsi = calculate_rsi(stock_data['close'])
    if 30 <= rsi <= 70:
        score += 20
    elif rsi < 30:
        score += 25  # 超卖反弹机会
    
    # KDJ评分 (0-20分)
    if kdj_golden_cross(stock_data):
        score += 20
    
    # 布林带评分 (0-15分)
    bb_position = bollinger_position(stock_data)
    if bb_position == 'near_lower':
        score += 15
    elif bb_position == 'break_middle':
        score += 12
    
    # 成交量评分 (0-10分)
    if volume_amplified(stock_data):
        score += 10
    
    # 均线评分 (0-10分)
    if ma_bullish_arrangement(stock_data):
        score += 10
    
    return score
```

### 2. 每日选股流程
```python
def daily_stock_selection():
    # 1. 获取全市场股票列表
    all_stocks = get_stock_list()
    
    # 2. 基础过滤
    filtered_stocks = basic_filter(all_stocks)
    
    # 3. 计算每只股票评分
    scored_stocks = []
    for stock in filtered_stocks:
        data = get_stock_data(stock, days=60)
        score = calculate_stock_score(data)
        if score >= 70:  # 评分阈值
            scored_stocks.append({
                'code': stock,
                'score': score,
                'name': get_stock_name(stock)
            })
    
    # 4. 按评分排序，取前10名
    top_stocks = sorted(scored_stocks, 
                       key=lambda x: x['score'], 
                       reverse=True)[:10]
    
    return top_stocks
```

## 🖥️ 简单Web界面

### 1. 每日选股结果展示
```html
<!DOCTYPE html>
<html>
<head>
    <title>今日推荐股票</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts/dist/echarts.min.js"></script>
</head>
<body>
    <div class="container">
        <h1>📈 今日选股推荐 - {{date}}</h1>
        
        <div class="stock-list">
            {% for stock in recommendations %}
            <div class="stock-card">
                <h3>{{stock.name}} ({{stock.code}})</h3>
                <p>评分: {{stock.score}}/100</p>
                <p>当前价格: ¥{{stock.price}}</p>
                <p>推荐理由: {{stock.reason}}</p>
            </div>
            {% endfor %}
        </div>
        
        <div class="chart-container">
            <div id="scoreChart"></div>
        </div>
    </div>
</body>
</html>
```

### 2. 股票详情页面
- K线图展示
- 技术指标图表
- 买卖信号标记
- 风险提示

## ⏰ 自动化运行

### 1. 定时任务设置
```python
# 使用schedule库实现定时任务
import schedule
import time

def run_daily_selection():
    """每日选股主函数"""
    print(f"开始执行每日选股 - {datetime.now()}")
    
    # 执行选股
    recommendations = daily_stock_selection()
    
    # 保存结果
    save_results(recommendations)
    
    # 发送通知
    send_notification(recommendations)
    
    print(f"选股完成，推荐{len(recommendations)}只股票")

# 设置每个交易日上午9:30执行
schedule.every().monday.at("09:30").do(run_daily_selection)
schedule.every().tuesday.at("09:30").do(run_daily_selection)
schedule.every().wednesday.at("09:30").do(run_daily_selection)
schedule.every().thursday.at("09:30").do(run_daily_selection)
schedule.every().friday.at("09:30").do(run_daily_selection)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### 2. 通知推送
```python
def send_notification(stocks):
    """发送选股结果通知"""
    
    # 邮件通知
    email_content = generate_email_report(stocks)
    send_email("your_email@example.com", "今日推荐股票", email_content)
    
    # 微信通知（可选）
    wechat_message = generate_wechat_message(stocks)
    send_wechat_message(wechat_message)
```

## 🚀 快速部署指南

### 1. 环境准备
```bash
# 安装Python依赖
pip install akshare pandas talib flask schedule requests

# 克隆项目
git clone <your-repo>
cd personal_stock_selector
```

### 2. 配置文件
```python
# config.py
CONFIG = {
    'email': {
        'smtp_server': 'smtp.gmail.com',
        'port': 587,
        'username': 'your_email@gmail.com',
        'password': 'your_app_password',
        'to_email': 'your_email@gmail.com'
    },
    'stock_filter': {
        'min_market_cap': 5000000000,  # 50亿
        'max_recent_gain': 0.3,        # 30%
        'min_score': 70                # 最低评分
    }
}
```

### 3. 启动系统
```bash
# 启动Web服务
python web_app.py

# 启动定时选股任务
python main.py
```

## 📱 使用体验

### 1. 每日工作流
1. **早上9:30** - 系统自动运行选股
2. **9:35** - 收到邮件/微信推荐结果
3. **随时** - 访问web页面查看详细分析
4. **盘中** - 根据推荐进行操作决策

### 2. 推荐结果示例
```
📈 今日选股推荐 - 2024-01-15

🥇 平安银行 (000001) - 评分: 88/100
   当前价格: ¥12.56
   推荐理由: MACD金叉+RSI超卖反弹+成交量放大

🥈 比亚迪 (002594) - 评分: 85/100
   当前价格: ¥245.30
   推荐理由: 布林带下轨反弹+KDJ金叉+均线多头

🥉 招商银行 (600036) - 评分: 82/100
   当前价格: ¥35.67
   推荐理由: MACD金叉+均线多头排列
```

## ⚠️ 风险提示

1. **技术指标的局限性**: 指标存在滞后性，可能出现假信号
2. **市场风险**: 股市有风险，技术分析不能保证收益
3. **系统性风险**: 大盘下跌时个股难以独善其身
4. **建议**: 仅供参考，请结合基本面分析和个人判断

## 🔄 后续优化方向

1. **增加基本面指标**: PE、PB、ROE等财务指标
2. **机器学习优化**: 使用历史数据训练选股模型
3. **回测功能**: 验证策略历史表现
4. **资金管理**: 添加仓位管理建议
5. **行业轮动**: 根据板块强弱调整选股偏好

这个个人选股系统专注于实用性和自动化，让您每天都能轻松获得基于技术分析的股票推荐！ 