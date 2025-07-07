"""
增强版用户配置文件 - 四维选股模型
技术面60% + 基本面25% + 市场情绪10% + 行业5%
"""

from datetime import time

# 增强版选股配置
STOCK_FILTER = {
    'min_market_cap': 8000000000,    # 80亿市值（更安全）
    'max_recent_gain': 25,           # 25%涨幅上限（避免追高）
    'min_score': 75,                 # 75分最低分（更严格）
    'max_stocks': 8,                 # 8只精选股票
    'analysis_period': 60,           # 60天分析周期
    
    # 基本面要求（新增）
    'max_pe': 30,                    # PE不超过30倍
    'min_roe': 5,                    # ROE不低于5%
    'max_pb': 5,                     # PB不超过5倍
}

# 增强版权重配置（四维模型）
INDICATOR_WEIGHTS = {
    # 技术面 (60%)
    'macd': 0.10,           # MACD权重降低
    'rsi': 0.08,            # RSI权重降低
    'kdj': 0.08,            # KDJ权重降低
    'bollinger': 0.06,      # 布林带权重降低
    'volume': 0.12,         # 成交量权重大幅提升 ⭐
    'ma': 0.06,             # 均线权重保持
    'adx': 0.10,            # 新增ADX趋势强度 ⭐
    
    # 基本面 (25%) - 新增安全网
    'fundamentals': 0.25,   # 基本面评分 ⭐
    
    # 市场情绪 (10%) - 新增
    'sentiment': 0.10,      # 市场情绪评分 ⭐
    
    # 行业轮动 (5%) - 新增
    'industry': 0.05        # 行业强度评分 ⭐
}

# 优化版MACD参数
MACD_PARAMS = {
    'fast': 9,      # 快线9（原12）
    'slow': 19,     # 慢线19（原26）
    'signal': 6     # 信号6（原9）
}

# 邮件通知配置（可选）
EMAIL_CONFIG = {
    'enabled': False,  # 改为True开启邮件通知
    'username': 'your_email@gmail.com',     # 您的邮箱
    'password': 'your_app_password',        # 应用密码
    'to_email': 'your_email@gmail.com',     # 接收邮箱
    'subject_template': '🏆 增强版选股推荐 - {date}',
}

# 定时任务配置
SCHEDULE_CONFIG = {
    'enabled': True,
    'run_time': time(9, 35),    # 9:35执行
    'weekdays_only': True,
}
