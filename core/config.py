"""
个人选股系统配置文件
包含系统配置、选股参数、通知设置等
"""

import os
from datetime import time

class Config:
    """统一配置管理"""
    # --- 应用基础配置 ---
    APP_NAME = "A股智能选股系统"
    VERSION = "3.0.0"
    DEBUG = True
    
    # --- Web界面配置 ---
    WEB_CONFIG = {
        'secret_key': os.urandom(24)
    }

    # --- 数据获取配置 ---
    DATA_FETCHER_CONFIG = {
        'cache_path': 'cache',
        'cache_expiry_hours': 4,
        'rate_limit_per_minute': 60,
    }

    # --- 默认邮件通知配置 ---
    # 用户可以在 user_config.py 中覆盖
    EMAIL_CONFIG = {
        'enabled': False,
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'to_email': '',
        'use_tls': True,
        'subject_template': '📈 每日选股推荐 - {date}',
    }
    
    # --- 默认定时任务配置 ---
    SCHEDULE_CONFIG = {
        'enabled': True,
        'run_time': time(9, 30),
        'weekdays_only': True,
        'timezone': 'Asia/Shanghai'
    }
    
    # --- 策略默认配置 ---
    # 策略1: 纯技术分析策略 (原基础版)
    TECHNICAL_STRATEGY_CONFIG = {
        'period': 60,
        'top_n': 10,
        'max_market_cap': 200 * 100000000,
        'indicators': [
            {"kind": "sma", "length": 5},
            {"kind": "sma", "length": 10},
            {"kind": "sma", "length": 20},
            {"kind": "macd"},
            {"kind": "rsi"},
            {"kind": "kdj"}
        ]
    }
    
    # 策略2: 四维综合分析策略 (原增强版)
    COMPREHENSIVE_STRATEGY_CONFIG = {
        'strategy_name': 'comprehensive',
        'display_name': '四维综合分析策略',
        
        # 基础运行参数
        'analysis_period': 90,
        'max_stocks': 8,

        # 基础筛选条件
        'min_market_cap': 8000000000,    # 80亿市值
        'max_recent_gain': 25,           # 近期最大涨幅25%
        'min_score': 75,                 # 最低总评分75

        # 1. 技术面分析配置
        'technical_indicators': [
            {"kind": "sma", "length": 5},
            {"kind": "sma", "length": 10},
            {"kind": "sma", "length": 20},
            {"kind": "adx"},
            {"kind": "macd", "fast": 9, "slow": 19, "signal": 6}, # 使用优化参数
            {"kind": "rsi"},
            {"kind": "kdj"}
        ],
        
        # 2. 基本面筛选配置 (新增)
        'fundamental_filters': {
            'max_pe_ttm': 30,
            'min_roe': 5,
            'max_pb': 5,
            'max_debt_ratio': 0.6 # 资产负债率
        },

        # 3. 市场情绪分析配置 (占位)
        'sentiment_config': {},

        # 4. 行业分析配置 (占位)
        'industry_config': {},

        # 四维权重配置
        'weights': {
            'technical': 0.60,
            'fundamental': 0.25,
            'sentiment': 0.10,
            'industry': 0.05
        }
    }

    def __init__(self):
        self.load_user_config()

    def load_user_config(self):
        """
        动态加载用户配置文件 (user_config.py)，并用其覆盖默认配置。
        这样用户就可以在不修改项目源码的情况下自定义配置。
        """
        try:
            from user_config import USER_CONFIG
            print("✅ 成功加载 `user_config.py` 用户配置文件。")

            # 递归地更新配置字典
            def update_dict(d, u):
                for k, v in u.items():
                    if isinstance(v, dict):
                        d[k] = update_dict(d.get(k, {}), v)
                    else:
                        d[k] = v
                return d

            # 遍历用户配置，更新到Config类属性中
            for key, value in USER_CONFIG.items():
                if hasattr(self, key):
                    current_value = getattr(self, key)
                    if isinstance(current_value, dict) and isinstance(value, dict):
                        update_dict(current_value, value)
                    else:
                        setattr(self, key, value)

        except ImportError:
            print("ℹ️ 未找到 `user_config.py`，将使用系统默认配置。")
        except Exception as e:
            print(f"❌ 加载用户配置 `user_config.py` 时出错: {e}")
        
# 全局配置实例
config = Config()

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
    config.load_user_config()
    
    # 验证配置
    Config.validate_config()
    
    print("配置初始化完成")

def get_strategy_config(strategy_name: str):
    """
    根据策略名称获取对应的配置字典
    """
    if strategy_name == 'technical':
        return config.TECHNICAL_STRATEGY_CONFIG
    elif strategy_name == 'comprehensive':
        return config.COMPREHENSIVE_STRATEGY_CONFIG
    else:
        raise ValueError(f"未知的策略名称: {strategy_name}")

if __name__ == "__main__":
    init_config() 