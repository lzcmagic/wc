"""
个人选股系统配置文件
统一管理应用配置，使用新的环境配置和策略配置系统
"""

import os
from datetime import time

# 导入新的配置模块
from core.env_config import env_config
from core.strategy_config import strategy_config

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


    
    # --- 定时任务配置 (从策略配置获取) ---
    @property
    def SCHEDULE_CONFIG(self):
        """动态获取定时任务配置"""
        return strategy_config.SCHEDULE_CONFIG
    
    # --- 策略配置 (从策略配置模块获取) ---
    @property
    def TECHNICAL_STRATEGY_CONFIG(self):
        """获取技术分析策略配置"""
        return strategy_config.get_strategy_config('technical')
    
    @property
    def COMPREHENSIVE_STRATEGY_CONFIG(self):
        """获取综合分析策略配置"""
        return strategy_config.get_strategy_config('comprehensive')

    @staticmethod
    def create_directories():
        """创建必要的目录"""
        dirs = ['cache', 'results', 'logs']
        for dir_name in dirs:
            if not os.path.exists(dir_name):
                os.makedirs(dir_name)
                print(f"创建目录: {dir_name}")

    @staticmethod
    def validate_config():
        """验证配置完整性"""
        print("配置验证完成")

    def __init__(self):
        """初始化配置系统"""
        # 打印配置状态
        self.print_config_status()

    def print_config_status(self):
        """打印配置状态"""
        print("🔧 配置系统状态:")
        print(f"   应用名称: {self.APP_NAME}")
        print(f"   版本: {self.VERSION}")
        
        # 打印环境配置状态
        env_config.print_config_status()
        
        # 验证策略配置
        print("\n📋 策略配置状态:")
        for strategy_name in ['technical', 'comprehensive']:
            if strategy_config.validate_strategy_config(strategy_name):
                print(f"   ✅ {strategy_name} 策略配置完整")
            else:
                print(f"   ❌ {strategy_name} 策略配置有问题")
        
# 全局配置实例
config = Config()



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
    return strategy_config.get_strategy_config(strategy_name)

if __name__ == "__main__":
    init_config() 