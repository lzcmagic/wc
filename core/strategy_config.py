"""
选股策略配置模块
包含所有策略的配置参数，独立于环境配置
"""

from datetime import time

class StrategyConfig:
    """策略配置管理"""
    
    # --- 策略1: 纯技术分析策略 (原基础版) ---
    TECHNICAL_STRATEGY = {
        'strategy_name': 'technical',
        'display_name': '技术分析策略',
        
        # 基础运行参数
        'period': 60,
        'analysis_period': 60,
        'top_n': 10,
        'max_stocks': 10,
        
        # 基础筛选条件 (优化：提高门槛，减少候选股票数量)
        'min_market_cap': 5000000000,       # 50亿 (提高最低市值要求)
        'max_market_cap': 150 * 100000000,  # 150亿 (降低上限，聚焦中盘股)
        'max_recent_gain': 20,              # 20% (降低涨幅限制，排除过热股票)
        'min_score': 65,                    # 最低评分65分 (提高评分门槛)
        
        # 技术指标配置
        'indicators': [
            {"kind": "sma", "length": 5},
            {"kind": "sma", "length": 10},
            {"kind": "sma", "length": 20},
            {"kind": "macd"},
            {"kind": "rsi"},
            {"kind": "kdj"}
        ],
        
        # API调用控制
        'api_call_delay': 1.0,  # 增加到1秒，减少API压力
        'max_workers': 8,       # 减少并发线程数，配合更长的延迟
        'sample_size': 80,              # 减少采样数量
        'max_filtered_stocks': 30,      # 减少候选股票数量
        'min_data_days': 30,
        'recent_gain_days': 30
    }
    
    # --- 策略2: 四维综合分析策略 (原增强版) ---
    COMPREHENSIVE_STRATEGY = {
        'strategy_name': 'comprehensive',
        'display_name': '四维综合分析策略',
        
        # 基础运行参数
        'analysis_period': 90,
        'max_stocks': 8,

        # 基础筛选条件 (优化：适度放宽条件，增加候选股票池)
        'min_market_cap': 6000000000,    # 60亿市值 (适当降低门槛)
        'max_market_cap': 150 * 100000000, # 150亿 (扩大上限，增加选择空间)
        'max_recent_gain': 25,           # 近期最大涨幅25% (适当放宽)
        'min_score': 68,                 # 最低总评分68 (降低门槛，提高命中率)

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
        
        # 2. 基本面筛选配置
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
        },

        # API调用控制
        'api_call_delay': 1.0,  # 增加到1秒，减少API压力
        'max_workers': 6,       # 综合策略使用更少的并发线程
    }
    
    # --- 策略3: 短线交易策略 (新增) ---
    SHORT_TERM_STRATEGY = {
        'strategy_name': 'short_term',
        'display_name': '短线交易策略',
        
        # 基础运行参数
        'period': 20,                    # 只看20天数据，够用
        'analysis_period': 20,
        'max_stocks': 15,                # 多一些选择
        
        # 基础筛选条件 (短线专用)
        'min_market_cap': 2000000000,    # 20亿即可，中小盘更活跃
        'max_market_cap': 80000000000,   # 800亿以下，避免大象股
        'max_recent_gain': 50,           # 允许50%涨幅，抓妖股机会
        'min_score': 60,                 # 降低门槛，增加机会
        'min_turnover_rate': 3,          # 换手率>3%，活跃度要求
        'max_pe': 100,                   # PE放宽，成长股估值高正常
        
        # 短线专用技术指标配置
        'technical_indicators': [
            {"kind": "sma", "length": 5},
            {"kind": "sma", "length": 10},
            {"kind": "macd", "fast": 6, "slow": 12, "signal": 4}, # 更敏感参数
            {"kind": "rsi", "length": 6},    # 更短周期RSI
            {"kind": "kdj", "length": 6},    # 更短周期KDJ
            {"kind": "bbands", "length": 10, "std": 1.5}  # 短期布林带
        ],
        
        # 短线专用权重配置 - 重成交量轻基本面
        'weights': {
            'volume_momentum': 0.25,     # 成交量动量 - 最重要
            'price_momentum': 0.20,      # 价格动量 - 短期趋势
            'technical_breakthrough': 0.20, # 技术突破信号
            'market_sentiment': 0.15,    # 市场情绪/热点
            'liquidity': 0.10,          # 流动性指标
            'volatility': 0.10,         # 波动率 - 短线需要波动
        },
        
        # API调用控制
        'api_call_delay': 0.8,  # 稍快一些，短线时效性要求高
        'max_workers': 10,      # 增加并发，提高速度
        'sample_size': 120,     # 增加采样，短线需要更多机会
        'max_filtered_stocks': 50,  # 增加候选数量
        'min_data_days': 15,    # 减少最小数据天数
        'recent_gain_days': 5   # 缩短涨幅统计周期
    }
    
    # --- 定时任务配置 ---
    SCHEDULE_CONFIG = {
        'enabled': True,
        'run_time': time(9, 30),
        'weekdays_only': True,
        'timezone': 'Asia/Shanghai'
    }
    
    @classmethod
    def get_strategy_config(cls, strategy_name: str) -> dict:
        """根据策略名称获取配置"""
        if strategy_name == 'technical':
            return cls.TECHNICAL_STRATEGY.copy()
        elif strategy_name == 'comprehensive':
            return cls.COMPREHENSIVE_STRATEGY.copy()
        elif strategy_name == 'short_term':
            return cls.SHORT_TERM_STRATEGY.copy()
        else:
            raise ValueError(f"未知的策略名称: {strategy_name}")
    
    @classmethod
    def get_all_strategies(cls) -> dict:
        """获取所有策略配置"""
        return {
            'technical': cls.TECHNICAL_STRATEGY,
            'comprehensive': cls.COMPREHENSIVE_STRATEGY,
            'short_term': cls.SHORT_TERM_STRATEGY
        }
    
    @classmethod
    def validate_strategy_config(cls, strategy_name: str) -> bool:
        """验证策略配置完整性"""
        try:
            config = cls.get_strategy_config(strategy_name)
            
            # 检查必要字段
            required_fields = ['strategy_name', 'display_name', 'analysis_period', 'max_stocks', 'min_score']
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                print(f"❌ 策略 {strategy_name} 配置不完整，缺少字段: {', '.join(missing_fields)}")
                return False
                
            return True
            
        except ValueError as e:
            print(f"❌ 策略配置验证失败: {e}")
            return False

# 全局策略配置实例
strategy_config = StrategyConfig() 