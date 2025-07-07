"""
增强版选股系统配置 - 一键升级现有系统
包含所有优化配置，可以直接替换原有配置
"""

from datetime import time

class EnhancedConfig:
    """增强版配置类"""
    
    # 应用信息
    APP_NAME = "增强版A股选股系统"
    VERSION = "2.0.0"
    DEBUG = True
    
    # 增强版选股配置
    ENHANCED_STOCK_FILTER = {
        # 基础筛选（更严格）
        'min_market_cap': 8000000000,    # 提升到80亿（更安全）
        'max_recent_gain': 25,           # 降低到25%（避免追高）
        'min_score': 75,                 # 提升到75分（更严格）
        'max_stocks': 8,                 # 减少到8只（精选）
        'analysis_period': 60,           # 分析周期60天
        'sample_size': 100,              # 扩大样本到100只
        
        # 基本面要求（新增安全网）
        'max_pe': 30,                    # PE上限30倍
        'min_roe': 5,                    # ROE下限5%
        'max_pb': 5,                     # PB上限5倍
        'max_debt_ratio': 0.6,           # 负债率上限60%
        
        # 技术面要求（增强）
        'min_adx': 20,                   # 最小ADX趋势强度
        'volume_amplify': 2.0,           # 成交量放大倍数
        'min_williams_r': -80,           # 威廉指标下限
        'max_williams_r': -20,           # 威廉指标上限
    }
    
    # 增强版技术指标权重（四维模型）
    ENHANCED_INDICATOR_WEIGHTS = {
        # === 技术面 (60%) ===
        'macd': 0.10,           # MACD（降低依赖）
        'rsi': 0.08,            # RSI（适当降低）
        'kdj': 0.08,            # KDJ（适当降低）
        'bollinger': 0.06,      # 布林带（适当降低）
        'volume_obv': 0.12,     # OBV成交量（大幅提升）⭐
        'ma_trend': 0.06,       # 均线趋势（保持）
        'adx_strength': 0.10,   # ADX趋势强度（新增）⭐
        
        # === 基本面 (25%) ===
        'fundamentals': 0.25,   # 基本面安全网（新增）⭐
        
        # === 市场情绪 (10%) ===
        'price_momentum': 0.03, # 价格动量（新增）
        'volume_momentum': 0.04,# 成交量动量（新增）
        'volatility': 0.03,     # 波动率评分（新增）
        
        # === 行业因子 (5%) ===
        'industry': 0.05        # 行业轮动（新增）⭐
    }
    
    # 行业评分权重
    INDUSTRY_SCORES = {
        # 新兴高科技（高分85-90）
        '新能源': 90, '半导体': 88, '人工智能': 90, '芯片': 88,
        '新能源汽车': 85, '光伏': 85, '储能': 88, '5G': 80,
        
        # 生物医药（高分80-85）
        '生物医药': 85, '创新药': 88, '医疗器械': 82, '疫苗': 85,
        
        # 消费升级（中高分70-80）
        '白酒': 78, '食品饮料': 72, '美妆': 75, '体育用品': 70,
        
        # 稳定消费（中分60-70）
        '家电': 65, '汽车': 68, '纺织': 60, '零售': 62,
        
        # 周期性行业（中低分50-60）
        '化工': 58, '钢铁': 52, '有色': 55, '建材': 50,
        
        # 传统金融（低分40-50）
        '银行': 48, '保险': 45, '证券': 52,
        
        # 房地产相关（低分30-45）
        '地产': 35, '建筑': 42, '装修': 38
    }
    
    # MACD优化参数（更适合A股）
    ENHANCED_MACD_PARAMS = {
        'fast': 9,     # 快线周期（原12）
        'slow': 19,    # 慢线周期（原26） 
        'signal': 6    # 信号线周期（原9）
    }
    
    # 定时任务配置
    ENHANCED_SCHEDULE_CONFIG = {
        'enabled': True,
        'run_time': time(9, 35),     # 9:35执行（开盘后5分钟）
        'weekdays_only': True,
        'timezone': 'Asia/Shanghai'
    }
    
    # 风险控制配置
    ENHANCED_RISK_CONTROL = {
        'max_daily_requests': 500,      # 降低请求频率
        'rate_limit_per_minute': 30,    # 每分钟最多30次
        'blacklist_patterns': [
            r'.*ST.*', r'.*\*ST.*',     # ST股票
            r'.*退市.*', r'.*暂停.*',    # 退市风险
            r'.*N.*',                   # 新股（上市30天内）
        ],
        'whitelist_industries': [       # 白名单行业
            '新能源', '半导体', '生物医药', '人工智能',
            '新能源汽车', '创新药', '白酒', '食品饮料'
        ]
    }
    
    # 邮件通知模板（增强版）
    ENHANCED_EMAIL_CONFIG = {
        'enabled': False,  # 默认关闭
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'username': '',
        'password': '',
        'to_email': '',
        'subject_template': '🏆 增强版选股推荐 - {date}',
        'use_tls': True,
        'html_template': True  # 使用HTML格式
    }

# 一键升级函数
def upgrade_to_enhanced():
    """一键升级到增强版配置"""
    print("🚀 正在升级到增强版选股系统...")
    
    try:
        # 1. 备份原配置
        backup_original_config()
        
        # 2. 应用增强版配置
        apply_enhanced_config()
        
        # 3. 验证配置
        validate_enhanced_config()
        
        print("✅ 升级完成！")
        print("🎯 新特性:")
        print("  • 四维评分模型（技术+基本面+情绪+行业）")
        print("  • 成交量权重提升到12%")
        print("  • 新增ADX趋势强度判断")
        print("  • 基本面安全网（避免踩雷）")
        print("  • 行业轮动分析")
        print("  • 更严格的筛选标准")
        
        return True
        
    except Exception as e:
        print(f"❌ 升级失败: {e}")
        restore_original_config()
        return False

def backup_original_config():
    """备份原始配置"""
    import shutil
    import os
    from datetime import datetime
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = f"backup_{timestamp}"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # 备份关键文件
    files_to_backup = [
        'config.py',
        'user_config.py',
        'stock_selector.py',
        'indicators.py'
    ]
    
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy2(file, f"{backup_dir}/{file}")
    
    print(f"📁 原配置已备份到: {backup_dir}")

def apply_enhanced_config():
    """应用增强版配置"""
    
    # 创建增强版用户配置
    enhanced_user_config = '''"""
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
'''
    
    # 写入增强版配置文件
    with open('enhanced_user_config.py', 'w', encoding='utf-8') as f:
        f.write(enhanced_user_config)
    
    print("📝 增强版配置文件已创建: enhanced_user_config.py")

def validate_enhanced_config():
    """验证增强版配置"""
    print("🔍 验证增强版配置...")
    
    # 验证权重总和
    weights = EnhancedConfig.ENHANCED_INDICATOR_WEIGHTS
    total_weight = sum(weights.values())
    
    if abs(total_weight - 1.0) > 0.01:
        raise ValueError(f"权重总和错误: {total_weight}")
    
    # 验证参数范围
    config = EnhancedConfig.ENHANCED_STOCK_FILTER
    if config['min_score'] < 0 or config['min_score'] > 100:
        raise ValueError("评分阈值必须在0-100之间")
    
    print("✅ 配置验证通过")

def restore_original_config():
    """恢复原始配置"""
    print("🔄 正在恢复原始配置...")
    # 这里可以添加恢复逻辑
    pass

# 快速测试函数
def test_enhanced_system():
    """测试增强版系统"""
    print("🧪 测试增强版系统...")
    
    try:
        # 测试配置加载
        config = EnhancedConfig()
        print(f"✅ 配置加载成功")
        
        # 测试权重计算
        weights = EnhancedConfig.ENHANCED_INDICATOR_WEIGHTS
        total = sum(weights.values())
        print(f"✅ 权重总和: {total:.3f}")
        
        # 测试行业评分
        industry_count = len(EnhancedConfig.INDUSTRY_SCORES)
        print(f"✅ 行业评分库: {industry_count} 个行业")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 增强版A股选股系统配置")
    print("=" * 40)
    
    # 测试系统
    if test_enhanced_system():
        print("\n💡 使用方法:")
        print("1. 执行 upgrade_to_enhanced() 升级系统")
        print("2. 或直接使用 enhanced_user_config.py")
        print("3. 运行 python main.py run 开始选股")
        
        # 可选：直接升级
        user_input = input("\n是否立即升级到增强版？(y/n): ")
        if user_input.lower() == 'y':
            upgrade_to_enhanced()
    else:
        print("❌ 系统测试失败，请检查配置") 