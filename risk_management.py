#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险管理系统 - 智能投资风险控制
支持止损预警、仓位管理、风险评估、投资组合分析、VaR计算
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Tuple, Optional
import json
import os
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import akshare as ak
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "低风险"
    MEDIUM = "中等风险"
    HIGH = "高风险"
    EXTREME = "极高风险"

class AlertType(Enum):
    """预警类型枚举"""
    STOP_LOSS = "止损预警"
    POSITION_OVERWEIGHT = "仓位超重"
    VOLATILITY_HIGH = "波动率过高"
    CORRELATION_HIGH = "相关性过高"
    DRAWDOWN_LARGE = "大幅回撤"
    SECTOR_CONCENTRATION = "行业过度集中"

@dataclass
class Position:
    """持仓信息类"""
    code: str
    name: str
    quantity: int
    cost_price: float
    current_price: float
    market_value: float
    weight: float  # 在组合中的权重
    profit_loss: float
    profit_loss_pct: float
    stop_loss_price: float
    take_profit_price: float
    sector: str
    buy_date: str
    holding_days: int

@dataclass
class RiskMetrics:
    """风险指标类"""
    portfolio_value: float
    total_profit_loss: float
    total_profit_loss_pct: float
    max_drawdown: float
    current_drawdown: float
    volatility: float
    sharpe_ratio: float
    beta: float
    var_95: float  # 95%置信度VaR
    var_99: float  # 99%置信度VaR
    sector_concentration: Dict[str, float]
    position_concentration: float  # 最大单一持仓比例
    correlation_risk: float

@dataclass
class RiskAlert:
    """风险预警类"""
    alert_type: AlertType
    level: RiskLevel
    message: str
    stock_code: str
    current_value: float
    threshold_value: float
    suggestion: str
    timestamp: datetime

class PortfolioDatabase:
    """投资组合数据库管理"""
    
    def __init__(self, db_path: str = "portfolio.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建持仓表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                cost_price REAL NOT NULL,
                buy_date TEXT NOT NULL,
                sector TEXT DEFAULT '',
                stop_loss_price REAL DEFAULT 0,
                take_profit_price REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建交易记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,  -- BUY, SELL
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                amount REAL NOT NULL,
                fee REAL DEFAULT 0,
                trade_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建风险预警记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                stock_code TEXT NOT NULL,
                current_value REAL NOT NULL,
                threshold_value REAL NOT NULL,
                suggestion TEXT NOT NULL,
                is_handled BOOLEAN DEFAULT FALSE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_position(self, code: str, name: str, quantity: int, cost_price: float, 
                    buy_date: str, sector: str = "", stop_loss_price: float = 0, 
                    take_profit_price: float = 0):
        """添加持仓"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO positions (code, name, quantity, cost_price, buy_date, 
                                     sector, stop_loss_price, take_profit_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (code, name, quantity, cost_price, buy_date, sector, 
                  stop_loss_price, take_profit_price))
            
            conn.commit()
            conn.close()
            logger.info(f"添加持仓: {name} ({code})")
        except Exception as e:
            logger.error(f"添加持仓失败: {e}")
    
    def get_all_positions(self) -> List[Dict]:
        """获取所有持仓"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM positions')
            columns = [description[0] for description in cursor.description]
            positions = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            conn.close()
            return positions
        except Exception as e:
            logger.error(f"获取持仓失败: {e}")
            return []
    
    def add_risk_alert(self, alert: RiskAlert):
        """添加风险预警"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO risk_alerts (alert_type, level, message, stock_code,
                                       current_value, threshold_value, suggestion)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (alert.alert_type.value, alert.level.value, alert.message,
                  alert.stock_code, alert.current_value, alert.threshold_value,
                  alert.suggestion))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"添加风险预警失败: {e}")

class RiskCalculator:
    """风险计算器"""
    
    def __init__(self):
        self.market_data_cache = {}
    
    def get_stock_price(self, code: str) -> Optional[float]:
        """获取股票当前价格"""
        try:
            # 简化版本，实际应用中可以缓存数据
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == code]
            if not stock_data.empty:
                return float(stock_data['最新价'].iloc[0])
            return None
        except Exception as e:
            logger.error(f"获取股票价格失败 {code}: {e}")
            return None
    
    def get_stock_history(self, code: str, days: int = 60) -> Optional[pd.DataFrame]:
        """获取股票历史数据"""
        try:
            if code in self.market_data_cache:
                return self.market_data_cache[code]
            
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                   start_date=start_date, end_date=end_date)
            
            if df.empty:
                return None
            
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.sort_values('日期')
            
            # 缓存数据
            self.market_data_cache[code] = df
            
            return df
        except Exception as e:
            logger.error(f"获取历史数据失败 {code}: {e}")
            return None
    
    def calculate_volatility(self, prices: pd.Series, window: int = 20) -> float:
        """计算波动率"""
        try:
            returns = prices.pct_change().dropna()
            volatility = returns.rolling(window=window).std().iloc[-1] * np.sqrt(252)
            return volatility if not np.isnan(volatility) else 0
        except Exception:
            return 0
    
    def calculate_var(self, returns: pd.Series, confidence: float = 0.95) -> float:
        """计算VaR (Value at Risk)"""
        try:
            if len(returns) < 10:
                return 0
            return np.percentile(returns, (1 - confidence) * 100)
        except Exception:
            return 0
    
    def calculate_max_drawdown(self, prices: pd.Series) -> Tuple[float, float]:
        """计算最大回撤和当前回撤"""
        try:
            cumulative = (1 + prices.pct_change()).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            
            max_drawdown = drawdown.min()
            current_drawdown = drawdown.iloc[-1]
            
            return abs(max_drawdown), abs(current_drawdown)
        except Exception:
            return 0, 0
    
    def calculate_correlation_matrix(self, positions: List[Position]) -> pd.DataFrame:
        """计算持仓股票相关性矩阵"""
        try:
            if len(positions) < 2:
                return pd.DataFrame()
            
            # 获取所有股票的收益率数据
            returns_data = {}
            
            for pos in positions:
                df = self.get_stock_history(pos.code)
                if df is not None and len(df) > 20:
                    returns = df['收盘'].pct_change().dropna()
                    returns_data[pos.code] = returns
            
            if len(returns_data) < 2:
                return pd.DataFrame()
            
            # 构建收益率DataFrame
            returns_df = pd.DataFrame(returns_data)
            
            # 计算相关性矩阵
            correlation_matrix = returns_df.corr()
            
            return correlation_matrix
        except Exception as e:
            logger.error(f"计算相关性矩阵失败: {e}")
            return pd.DataFrame()

class RiskManager:
    """风险管理器主类"""
    
    def __init__(self):
        self.db = PortfolioDatabase()
        self.calculator = RiskCalculator()
        self.risk_limits = self.load_risk_limits()
    
    def load_risk_limits(self) -> Dict[str, float]:
        """加载风险限制设置"""
        default_limits = {
            'max_single_position': 0.2,  # 单一持仓最大比例20%
            'max_sector_concentration': 0.4,  # 单一行业最大比例40%
            'max_correlation': 0.8,  # 最大相关性80%
            'max_volatility': 0.3,  # 最大波动率30%
            'max_drawdown': 0.15,  # 最大回撤15%
            'stop_loss_pct': 0.1,  # 默认止损比例10%
            'var_limit': 0.05,  # VaR限制5%
        }
        
        # 尝试从文件加载配置
        config_file = 'risk_limits.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    loaded_limits = json.load(f)
                default_limits.update(loaded_limits)
            except Exception as e:
                logger.error(f"加载风险限制配置失败: {e}")
        
        return default_limits
    
    def save_risk_limits(self):
        """保存风险限制设置"""
        try:
            with open('risk_limits.json', 'w', encoding='utf-8') as f:
                json.dump(self.risk_limits, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存风险限制配置失败: {e}")
    
    def build_portfolio(self) -> List[Position]:
        """构建投资组合"""
        positions_data = self.db.get_all_positions()
        positions = []
        total_value = 0
        
        for pos_data in positions_data:
            # 获取当前价格
            current_price = self.calculator.get_stock_price(pos_data['code'])
            if current_price is None:
                current_price = pos_data['cost_price']  # 使用成本价作为fallback
            
            # 计算市值和盈亏
            market_value = current_price * pos_data['quantity']
            total_value += market_value
            
            profit_loss = market_value - (pos_data['cost_price'] * pos_data['quantity'])
            profit_loss_pct = profit_loss / (pos_data['cost_price'] * pos_data['quantity']) * 100
            
            # 计算持有天数
            buy_date = datetime.strptime(pos_data['buy_date'], '%Y-%m-%d')
            holding_days = (datetime.now() - buy_date).days
            
            position = Position(
                code=pos_data['code'],
                name=pos_data['name'],
                quantity=pos_data['quantity'],
                cost_price=pos_data['cost_price'],
                current_price=current_price,
                market_value=market_value,
                weight=0,  # 稍后计算
                profit_loss=profit_loss,
                profit_loss_pct=profit_loss_pct,
                stop_loss_price=pos_data['stop_loss_price'],
                take_profit_price=pos_data['take_profit_price'],
                sector=pos_data['sector'],
                buy_date=pos_data['buy_date'],
                holding_days=holding_days
            )
            
            positions.append(position)
        
        # 计算权重
        for position in positions:
            position.weight = position.market_value / total_value if total_value > 0 else 0
        
        return positions
    
    def calculate_portfolio_metrics(self, positions: List[Position]) -> RiskMetrics:
        """计算投资组合风险指标"""
        
        if not positions:
            return RiskMetrics(
                portfolio_value=0, total_profit_loss=0, total_profit_loss_pct=0,
                max_drawdown=0, current_drawdown=0, volatility=0, sharpe_ratio=0,
                beta=0, var_95=0, var_99=0, sector_concentration={},
                position_concentration=0, correlation_risk=0
            )
        
        # 基本指标
        portfolio_value = sum(pos.market_value for pos in positions)
        total_profit_loss = sum(pos.profit_loss for pos in positions)
        total_profit_loss_pct = total_profit_loss / (portfolio_value - total_profit_loss) * 100 if portfolio_value > total_profit_loss else 0
        
        # 计算行业集中度
        sector_values = {}
        for pos in positions:
            sector = pos.sector or "未分类"
            sector_values[sector] = sector_values.get(sector, 0) + pos.market_value
        
        sector_concentration = {
            sector: value / portfolio_value 
            for sector, value in sector_values.items()
        }
        
        # 最大单一持仓比例
        position_concentration = max(pos.weight for pos in positions) if positions else 0
        
        # 计算投资组合波动率和其他高级指标
        portfolio_returns = []
        portfolio_volatility = 0
        max_drawdown = 0
        current_drawdown = 0
        var_95 = 0
        var_99 = 0
        correlation_risk = 0
        
        try:
            # 获取投资组合历史收益率
            all_returns = []
            weights = [pos.weight for pos in positions]
            
            for pos in positions:
                df = self.calculator.get_stock_history(pos.code)
                if df is not None and len(df) > 20:
                    returns = df['收盘'].pct_change().dropna()
                    all_returns.append(returns.values)
            
            if all_returns and len(all_returns[0]) > 20:
                # 计算加权组合收益率
                min_length = min(len(returns) for returns in all_returns)
                portfolio_returns = np.zeros(min_length)
                
                for i, returns in enumerate(all_returns):
                    portfolio_returns += weights[i] * returns[-min_length:]
                
                # 计算波动率
                portfolio_volatility = np.std(portfolio_returns) * np.sqrt(252)
                
                # 计算VaR
                var_95 = self.calculator.calculate_var(pd.Series(portfolio_returns), 0.95)
                var_99 = self.calculator.calculate_var(pd.Series(portfolio_returns), 0.99)
                
                # 计算最大回撤
                cumulative_returns = np.cumprod(1 + portfolio_returns)
                max_drawdown, current_drawdown = self.calculator.calculate_max_drawdown(pd.Series(cumulative_returns))
            
            # 计算相关性风险
            correlation_matrix = self.calculator.calculate_correlation_matrix(positions)
            if not correlation_matrix.empty:
                # 计算平均相关性（排除对角线）
                corr_values = correlation_matrix.values
                n = len(corr_values)
                if n > 1:
                    total_corr = np.sum(corr_values) - np.trace(corr_values)  # 排除对角线
                    correlation_risk = total_corr / (n * (n - 1))  # 平均相关性
        
        except Exception as e:
            logger.error(f"计算高级风险指标失败: {e}")
        
        return RiskMetrics(
            portfolio_value=portfolio_value,
            total_profit_loss=total_profit_loss,
            total_profit_loss_pct=total_profit_loss_pct,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            volatility=portfolio_volatility,
            sharpe_ratio=0,  # 需要无风险利率计算
            beta=0,  # 需要市场指数数据计算
            var_95=abs(var_95),
            var_99=abs(var_99),
            sector_concentration=sector_concentration,
            position_concentration=position_concentration,
            correlation_risk=abs(correlation_risk)
        )
    
    def check_risk_alerts(self, positions: List[Position], metrics: RiskMetrics) -> List[RiskAlert]:
        """检查风险预警"""
        alerts = []
        current_time = datetime.now()
        
        # 1. 检查止损预警
        for pos in positions:
            if pos.stop_loss_price > 0 and pos.current_price <= pos.stop_loss_price:
                alert = RiskAlert(
                    alert_type=AlertType.STOP_LOSS,
                    level=RiskLevel.HIGH,
                    message=f"{pos.name}触发止损价位",
                    stock_code=pos.code,
                    current_value=pos.current_price,
                    threshold_value=pos.stop_loss_price,
                    suggestion=f"建议立即卖出{pos.name}，控制损失",
                    timestamp=current_time
                )
                alerts.append(alert)
        
        # 2. 检查仓位超重
        if metrics.position_concentration > self.risk_limits['max_single_position']:
            max_pos = max(positions, key=lambda x: x.weight)
            alert = RiskAlert(
                alert_type=AlertType.POSITION_OVERWEIGHT,
                level=RiskLevel.MEDIUM,
                message=f"单一持仓比例过高: {max_pos.name}",
                stock_code=max_pos.code,
                current_value=max_pos.weight,
                threshold_value=self.risk_limits['max_single_position'],
                suggestion=f"建议减少{max_pos.name}仓位，分散投资风险",
                timestamp=current_time
            )
            alerts.append(alert)
        
        # 3. 检查行业集中度
        for sector, concentration in metrics.sector_concentration.items():
            if concentration > self.risk_limits['max_sector_concentration']:
                alert = RiskAlert(
                    alert_type=AlertType.SECTOR_CONCENTRATION,
                    level=RiskLevel.MEDIUM,
                    message=f"行业集中度过高: {sector}",
                    stock_code="PORTFOLIO",
                    current_value=concentration,
                    threshold_value=self.risk_limits['max_sector_concentration'],
                    suggestion=f"建议减少{sector}行业配置，增加其他行业投资",
                    timestamp=current_time
                )
                alerts.append(alert)
        
        # 4. 检查波动率
        if metrics.volatility > self.risk_limits['max_volatility']:
            alert = RiskAlert(
                alert_type=AlertType.VOLATILITY_HIGH,
                level=RiskLevel.HIGH,
                message="投资组合波动率过高",
                stock_code="PORTFOLIO",
                current_value=metrics.volatility,
                threshold_value=self.risk_limits['max_volatility'],
                suggestion="建议增加低波动率资产，降低组合风险",
                timestamp=current_time
            )
            alerts.append(alert)
        
        # 5. 检查相关性
        if metrics.correlation_risk > self.risk_limits['max_correlation']:
            alert = RiskAlert(
                alert_type=AlertType.CORRELATION_HIGH,
                level=RiskLevel.MEDIUM,
                message="持仓股票相关性过高",
                stock_code="PORTFOLIO",
                current_value=metrics.correlation_risk,
                threshold_value=self.risk_limits['max_correlation'],
                suggestion="建议增加不相关资产，提高投资组合多样性",
                timestamp=current_time
            )
            alerts.append(alert)
        
        # 6. 检查回撤
        if metrics.current_drawdown > self.risk_limits['max_drawdown']:
            alert = RiskAlert(
                alert_type=AlertType.DRAWDOWN_LARGE,
                level=RiskLevel.HIGH,
                message="投资组合回撤过大",
                stock_code="PORTFOLIO",
                current_value=metrics.current_drawdown,
                threshold_value=self.risk_limits['max_drawdown'],
                suggestion="建议降低仓位，等待市场企稳",
                timestamp=current_time
            )
            alerts.append(alert)
        
        # 保存预警到数据库
        for alert in alerts:
            self.db.add_risk_alert(alert)
        
        return alerts
    
    def generate_risk_report(self, positions: List[Position], metrics: RiskMetrics, alerts: List[RiskAlert]) -> str:
        """生成风险管理报告"""
        
        report = f"""
⚠️ 投资组合风险管理报告
{'='*60}
📅 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💼 投资组合总值: ¥{metrics.portfolio_value:,.2f}

📊 基本指标:
   • 总盈亏: ¥{metrics.total_profit_loss:,.2f} ({metrics.total_profit_loss_pct:+.2f}%)
   • 持仓数量: {len(positions)} 只股票
   • 最大单仓: {metrics.position_concentration:.1%}
   • 平均相关性: {metrics.correlation_risk:.3f}

📉 风险指标:
   • 投资组合波动率: {metrics.volatility:.1%}
   • 最大回撤: {metrics.max_drawdown:.1%}
   • 当前回撤: {metrics.current_drawdown:.1%}
   • VaR (95%): {metrics.var_95:.1%}
   • VaR (99%): {metrics.var_99:.1%}

🏭 行业分布:
"""
        
        # 行业分布
        for sector, concentration in sorted(metrics.sector_concentration.items(), 
                                          key=lambda x: x[1], reverse=True):
            bar_length = int(concentration * 20)  # 20字符宽度的进度条
            bar = "█" * bar_length + "░" * (20 - bar_length)
            report += f"   {sector:<12} {bar} {concentration:6.1%}\n"
        
        # 持仓明细
        report += "\n📋 持仓明细:\n"
        for i, pos in enumerate(sorted(positions, key=lambda x: x.weight, reverse=True), 1):
            status = ""
            if pos.profit_loss_pct > 20:
                status = "🚀"
            elif pos.profit_loss_pct > 5:
                status = "📈"
            elif pos.profit_loss_pct < -10:
                status = "📉"
            elif pos.profit_loss_pct < -5:
                status = "⚠️"
            else:
                status = "➖"
            
            report += f"   {i:2d}. {status} {pos.name:<12} {pos.weight:6.1%} {pos.profit_loss_pct:+7.2f}% (持有{pos.holding_days}天)\n"
        
        # 风险预警
        if alerts:
            report += f"\n🚨 风险预警 ({len(alerts)}条):\n"
            for i, alert in enumerate(alerts, 1):
                level_emoji = {"低风险": "🟢", "中等风险": "🟡", "高风险": "🔴", "极高风险": "🚫"}
                emoji = level_emoji.get(alert.level.value, "⚠️")
                report += f"   {i}. {emoji} {alert.message}\n"
                report += f"      💡 建议: {alert.suggestion}\n"
        else:
            report += "\n✅ 当前无风险预警\n"
        
        # 风险评级
        risk_score = self._calculate_risk_score(metrics)
        if risk_score >= 80:
            risk_rating = "🔴 高风险"
        elif risk_score >= 60:
            risk_rating = "🟡 中等风险"
        elif risk_score >= 40:
            risk_rating = "🟢 低风险"
        else:
            risk_rating = "🔵 极低风险"
        
        report += f"\n📊 风险评级: {risk_rating} (评分: {risk_score:.0f}/100)\n"
        
        # 操作建议
        report += "\n💡 操作建议:\n"
        if len(alerts) == 0:
            report += "   • 当前投资组合风险在可控范围内\n"
            report += "   • 继续关注市场变化，及时调整仓位\n"
        else:
            report += "   • 优先处理高风险预警\n"
            report += "   • 考虑降低仓位或调整持仓结构\n"
            report += "   • 密切关注市场动向，准备应对措施\n"
        
        if metrics.correlation_risk > 0.6:
            report += "   • 增加不相关资产，提高组合多样性\n"
        
        if metrics.position_concentration > 0.15:
            report += "   • 考虑减少最大持仓，分散投资风险\n"
        
        report += "\n⚠️ 免责声明:\n"
        report += "   • 本报告仅供参考，不构成投资建议\n"
        report += "   • 投资有风险，决策需谨慎\n"
        report += "   • 建议结合市场环境和个人情况做决策\n"
        
        return report
    
    def _calculate_risk_score(self, metrics: RiskMetrics) -> float:
        """计算风险评分 (0-100, 越高风险越大)"""
        score = 0
        
        # 波动率评分 (25分)
        vol_score = min(25, metrics.volatility * 100)
        score += vol_score
        
        # 集中度评分 (25分)
        conc_score = min(25, metrics.position_concentration * 100)
        score += conc_score
        
        # 回撤评分 (25分)
        dd_score = min(25, metrics.current_drawdown * 100)
        score += dd_score
        
        # 相关性评分 (25分)
        corr_score = min(25, metrics.correlation_risk * 25)
        score += corr_score
        
        return score

def main():
    """主程序"""
    print("⚠️ 投资组合风险管理系统")
    print("="*50)
    
    risk_manager = RiskManager()
    
    while True:
        print("\n请选择功能:")
        print("1. 📊 风险分析报告")
        print("2. 🚨 查看风险预警")
        print("3. ➕ 添加持仓")
        print("4. 📋 查看持仓")
        print("5. ⚙️ 设置风险限制")
        print("6. 💾 导出报告")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-6): ").strip()
        
        if choice == "1":
            print("📊 正在生成风险分析报告...")
            positions = risk_manager.build_portfolio()
            
            if not positions:
                print("❌ 暂无持仓数据，请先添加持仓")
                continue
            
            metrics = risk_manager.calculate_portfolio_metrics(positions)
            alerts = risk_manager.check_risk_alerts(positions, metrics)
            report = risk_manager.generate_risk_report(positions, metrics, alerts)
            
            print(report)
        
        elif choice == "2":
            print("🚨 检查风险预警...")
            positions = risk_manager.build_portfolio()
            
            if not positions:
                print("❌ 暂无持仓数据")
                continue
            
            metrics = risk_manager.calculate_portfolio_metrics(positions)
            alerts = risk_manager.check_risk_alerts(positions, metrics)
            
            if alerts:
                print(f"\n发现 {len(alerts)} 条风险预警:")
                for i, alert in enumerate(alerts, 1):
                    print(f"\n{i}. {alert.alert_type.value} - {alert.level.value}")
                    print(f"   股票: {alert.stock_code}")
                    print(f"   信息: {alert.message}")
                    print(f"   建议: {alert.suggestion}")
            else:
                print("✅ 当前无风险预警")
        
        elif choice == "3":
            print("➕ 添加持仓")
            try:
                code = input("股票代码: ").strip()
                name = input("股票名称: ").strip()
                quantity = int(input("持仓数量: "))
                cost_price = float(input("成本价格: "))
                buy_date = input("买入日期 (YYYY-MM-DD): ").strip()
                sector = input("所属行业 (可选): ").strip()
                
                # 可选的止损止盈设置
                stop_loss_input = input("止损价格 (可选，直接回车跳过): ").strip()
                stop_loss_price = float(stop_loss_input) if stop_loss_input else 0
                
                take_profit_input = input("止盈价格 (可选，直接回车跳过): ").strip()
                take_profit_price = float(take_profit_input) if take_profit_input else 0
                
                risk_manager.db.add_position(
                    code, name, quantity, cost_price, buy_date, 
                    sector, stop_loss_price, take_profit_price
                )
                
                print("✅ 持仓添加成功!")
                
            except ValueError:
                print("❌ 输入格式错误，请重新输入")
            except Exception as e:
                print(f"❌ 添加失败: {e}")
        
        elif choice == "4":
            print("📋 当前持仓:")
            positions = risk_manager.build_portfolio()
            
            if not positions:
                print("暂无持仓")
            else:
                total_value = sum(pos.market_value for pos in positions)
                total_cost = sum(pos.cost_price * pos.quantity for pos in positions)
                total_profit = total_value - total_cost
                
                print(f"\n📊 组合概览:")
                print(f"   总市值: ¥{total_value:,.2f}")
                print(f"   总成本: ¥{total_cost:,.2f}")
                print(f"   总盈亏: ¥{total_profit:,.2f} ({total_profit/total_cost*100:+.2f}%)")
                
                print(f"\n持仓明细:")
                for i, pos in enumerate(positions, 1):
                    status = "📈" if pos.profit_loss > 0 else "📉" if pos.profit_loss < 0 else "➖"
                    print(f"   {i:2d}. {status} {pos.name} ({pos.code})")
                    print(f"       数量: {pos.quantity:,} | 成本: ¥{pos.cost_price:.2f} | 现价: ¥{pos.current_price:.2f}")
                    print(f"       市值: ¥{pos.market_value:,.2f} | 盈亏: ¥{pos.profit_loss:,.2f} ({pos.profit_loss_pct:+.2f}%)")
        
        elif choice == "0":
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 