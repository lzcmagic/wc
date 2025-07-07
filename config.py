"""
个人选股系统配置文件
包含系统配置、选股参数、通知设置等
"""

import os
from datetime import time

class Config:
    """配置类"""
    
    # 基础配置
    APP_NAME = "个人A股选股系统"
    VERSION = "1.0.0"
    DEBUG = True
    
    # 数据配置
    DATA_SOURCE = "akshare"  # 数据源
    MAX_RETRIES = 3          # 最大重试次数
    REQUEST_DELAY = 0.2      # 请求延迟（秒）
    
    # 选股配置
    STOCK_FILTER = {
        'min_market_cap': 5000000000,  # 最小市值（50亿）
        'max_recent_gain': 30,         # 最大近期涨幅（30%）
        'min_score': 70,               # 最低评分
        'max_stocks': 10,              # 最多推荐股票数
        'analysis_period': 60,         # 分析周期（天）
        'sample_size': 100             # 样本大小
    }
    
    # 技术指标权重
    INDICATOR_WEIGHTS = {
        'macd': 0.25,      # MACD权重
        'rsi': 0.20,       # RSI权重
        'kdj': 0.20,       # KDJ权重
        'bollinger': 0.15, # 布林带权重
        'volume': 0.10,    # 成交量权重
        'ma': 0.10         # 均线权重
    }
    
    # 定时任务配置
    SCHEDULE_CONFIG = {
        'enabled': True,
        'run_time': time(9, 30),  # 每日运行时间 9:30
        'weekdays_only': True,    # 仅工作日运行
        'timezone': 'Asia/Shanghai'
    }
    
    # 文件路径配置
    PATHS = {
        'results_dir': 'results',
        'logs_dir': 'logs',
        'data_cache_dir': 'cache',
        'templates_dir': 'templates',
        'static_dir': 'static'
    }
    
    # Web应用配置
    WEB_CONFIG = {
        'host': '127.0.0.1',
        'port': 5000,
        'debug': DEBUG,
        'secret_key': 'your-secret-key-here'
    }
    
    # 邮件通知配置
    EMAIL_CONFIG = {
        'enabled': False,  # 默认关闭，需要用户配置
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': '',    # 需要用户设置
        'password': '',    # 需要用户设置
        'to_email': '',    # 需要用户设置
        'subject_template': '📈 今日选股推荐 - {date}',
        'use_tls': True
    }
    
    # 微信通知配置（可选）
    WECHAT_CONFIG = {
        'enabled': False,
        'webhook_url': '',  # 企业微信机器人webhook
        'at_mobiles': [],   # @指定手机号
        'at_all': False
    }
    
    # 日志配置
    LOGGING_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file_handler': {
            'enabled': True,
            'filename': 'logs/stock_selector.log',
            'max_bytes': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5
        },
        'console_handler': {
            'enabled': True
        }
    }
    
    # 风险控制配置
    RISK_CONTROL = {
        'max_daily_requests': 1000,    # 每日最大请求数
        'rate_limit_per_minute': 60,   # 每分钟最大请求数
        'blacklist_patterns': [        # 黑名单模式
            r'.*ST.*',     # ST股票
            r'.*退市.*',   # 退市股票
            r'.*暂停.*'    # 暂停上市
        ]
    }
    
    @staticmethod
    def create_directories():
        """创建必要的目录"""
        for path in Config.PATHS.values():
            if not os.path.exists(path):
                os.makedirs(path)
                print(f"创建目录: {path}")
    
    @staticmethod
    def load_user_config(config_file='user_config.py'):
        """加载用户自定义配置"""
        if os.path.exists(config_file):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("user_config", config_file)
                if spec is None or spec.loader is None:
                    raise ImportError(f"无法加载配置文件: {config_file}")
                user_config = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_config)
                
                # 更新邮件配置
                if hasattr(user_config, 'EMAIL_CONFIG'):
                    Config.EMAIL_CONFIG.update(user_config.EMAIL_CONFIG)
                
                # 更新选股配置
                if hasattr(user_config, 'STOCK_FILTER'):
                    Config.STOCK_FILTER.update(user_config.STOCK_FILTER)
                
                # 更新其他配置
                if hasattr(user_config, 'SCHEDULE_CONFIG'):
                    Config.SCHEDULE_CONFIG.update(user_config.SCHEDULE_CONFIG)
                
                print(f"已加载用户配置: {config_file}")
                
            except Exception as e:
                print(f"加载用户配置失败: {e}")
        else:
            print("未找到用户配置文件，使用默认配置")
    
    @staticmethod
    def validate_config():
        """验证配置有效性"""
        errors = []
        
        # 验证邮件配置
        if Config.EMAIL_CONFIG['enabled']:
            required_fields = ['username', 'password', 'to_email']
            for field in required_fields:
                if not Config.EMAIL_CONFIG.get(field):
                    errors.append(f"邮件配置缺少必填字段: {field}")
        
        # 验证选股参数
        if Config.STOCK_FILTER['min_score'] < 0 or Config.STOCK_FILTER['min_score'] > 100:
            errors.append("最低评分必须在0-100之间")
        
        if Config.STOCK_FILTER['max_stocks'] < 1:
            errors.append("最多推荐股票数必须大于0")
        
        # 验证权重总和
        weight_sum = sum(Config.INDICATOR_WEIGHTS.values())
        if abs(weight_sum - 1.0) > 0.01:
            errors.append(f"技术指标权重总和应为1.0，当前为: {weight_sum}")
        
        if errors:
            print("配置验证失败:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        print("配置验证通过")
        return True


# 用户配置模板
USER_CONFIG_TEMPLATE = '''"""
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
'''

def create_user_config_template():
    """创建用户配置模板文件"""
    template_file = 'user_config_template.py'
    if not os.path.exists(template_file):
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write(USER_CONFIG_TEMPLATE)
        print(f"已创建用户配置模板: {template_file}")
        print("请复制为 user_config.py 并修改相应配置")

# 初始化配置
def init_config():
    """初始化配置"""
    print("初始化配置...")
    
    # 创建目录
    Config.create_directories()
    
    # 创建用户配置模板
    create_user_config_template()
    
    # 加载用户配置
    Config.load_user_config()
    
    # 验证配置
    Config.validate_config()
    
    print("配置初始化完成")

if __name__ == "__main__":
    init_config() 