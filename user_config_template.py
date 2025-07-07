"""
用户自定义配置文件
复制此文件为 user_config.py 并修改相应配置
"""

# 邮件通知配置
EMAIL_CONFIG = {
    'enabled': True,  # 开启邮件通知
    'username': 'your_email@gmail.com',     # 发送邮箱
    'password': 'your_app_password',        # 邮箱应用密码
    'to_email': 'your_email@gmail.com',     # 接收邮箱
}

# 选股参数调整
STOCK_FILTER = {
    'min_market_cap': 3000000000,  # 降低市值要求到30亿
    'max_recent_gain': 40,         # 允许更高涨幅
    'min_score': 65,               # 降低评分要求
    'max_stocks': 8,               # 推荐8只股票
}

# 定时任务配置
SCHEDULE_CONFIG = {
    'enabled': True,
    'run_time': time(9, 45),  # 修改为9:45运行
    'weekdays_only': True,
}
