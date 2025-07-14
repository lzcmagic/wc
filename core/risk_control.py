"""
智能风险控制模块
提供多维度风险评估和控制机制
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

class RiskController:
    """智能风险控制器"""
    
    def __init__(self):
        self.max_position_weight = 0.15  # 单只股票最大仓位
        self.max_sector_weight = 0.30    # 单个行业最大仓位
        self.max_portfolio_volatility = 0.25  # 组合最大年化波动率
        self.max_correlation = 0.70      # 股票间最大相关系数
        
    def evaluate_portfolio_risk(self, selected_stocks: List[Dict], 
                               historical_data: Dict) -> Dict:
        """
        评估投资组合风险
        
        Args:
            selected_stocks: 选中的股票列表
            historical_data: 历史价格数据
            
        Returns:
            风险评估结果
        """
        risk_metrics = {}
        
        # 1. 个股风险评估
        individual_risks = self._assess_individual_risks(selected_stocks, historical_data)
        
        # 2. 组合波动率计算
        portfolio_volatility = self._calculate_portfolio_volatility(selected_stocks, historical_data)
        
        # 3. 相关性分析
        correlation_matrix = self._calculate_correlation_matrix(selected_stocks, historical_data)
        
        # 4. 行业集中度检查
        sector_concentration = self._check_sector_concentration(selected_stocks)
        
        # 5. VaR计算
        var_95, cvar_95 = self._calculate_var_cvar(selected_stocks, historical_data)
        
        # 6. 最大回撤预测
        max_drawdown_estimate = self._estimate_max_drawdown(selected_stocks, historical_data)
        
        risk_metrics = {
            'individual_risks': individual_risks,
            'portfolio_volatility': portfolio_volatility,
            'correlation_matrix': correlation_matrix,
            'sector_concentration': sector_concentration,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'max_drawdown_estimate': max_drawdown_estimate,
            'risk_score': self._calculate_overall_risk_score(portfolio_volatility, max_drawdown_estimate)
        }
        
        return risk_metrics
    
    def optimize_portfolio_weights(self, selected_stocks: List[Dict],
                                 historical_data: Dict) -> List[Dict]:
        """
        优化投资组合权重
        使用风险平价或最小方差优化
        """
        # 1. 计算协方差矩阵
        returns_data = self._prepare_returns_data(selected_stocks, historical_data)
        cov_matrix = returns_data.cov().values
        
        # 2. 使用风险平价模型优化权重
        optimal_weights = self._risk_parity_optimization(cov_matrix)
        
        # 3. 应用约束条件
        constrained_weights = self._apply_constraints(optimal_weights, selected_stocks)
        
        # 4. 更新股票权重
        for i, stock in enumerate(selected_stocks):
            stock['optimal_weight'] = constrained_weights[i]
            stock['risk_contribution'] = self._calculate_risk_contribution(
                constrained_weights[i], cov_matrix, i
            )
        
        return selected_stocks
    
    def _assess_individual_risks(self, selected_stocks: List[Dict], 
                               historical_data: Dict) -> Dict:
        """评估个股风险"""
        individual_risks = {}
        
        for stock in selected_stocks:
            code = stock['code']
            if code in historical_data:
                price_data = historical_data[code]
                
                # 计算波动率
                returns = price_data['close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)  # 年化波动率
                
                # 计算最大回撤
                cumulative_returns = (1 + returns).cumprod()
                rolling_max = cumulative_returns.expanding().max()
                drawdowns = (cumulative_returns - rolling_max) / rolling_max
                max_drawdown = drawdowns.min()
                
                # 计算Beta值（相对于市场）
                # 这里需要市场指数数据，暂时使用简化版本
                beta = self._calculate_beta(returns)
                
                # VaR计算
                var_95 = returns.quantile(0.05)
                
                individual_risks[code] = {
                    'volatility': volatility,
                    'max_drawdown': max_drawdown,
                    'beta': beta,
                    'var_95': var_95,
                    'risk_level': self._classify_risk_level(volatility, max_drawdown)
                }
        
        return individual_risks
    
    def _calculate_portfolio_volatility(self, selected_stocks: List[Dict],
                                      historical_data: Dict) -> float:
        """计算组合波动率"""
        returns_data = self._prepare_returns_data(selected_stocks, historical_data)
        
        if returns_data.empty:
            return 0
        
        # 等权重组合（后续可以优化权重）
        weights = np.array([1/len(selected_stocks)] * len(selected_stocks))
        
        # 计算组合波动率
        cov_matrix = returns_data.cov().values
        portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
        portfolio_volatility = np.sqrt(portfolio_variance) * np.sqrt(252)  # 年化
        
        return portfolio_volatility
    
    def _calculate_correlation_matrix(self, selected_stocks: List[Dict],
                                    historical_data: Dict) -> np.ndarray:
        """计算相关系数矩阵"""
        returns_data = self._prepare_returns_data(selected_stocks, historical_data)
        
        if returns_data.empty:
            return np.array([])
        
        correlation_matrix = returns_data.corr().values
        return correlation_matrix
    
    def _check_sector_concentration(self, selected_stocks: List[Dict]) -> Dict:
        """检查行业集中度"""
        sector_weights = {}
        total_weight = len(selected_stocks)  # 简化为等权重
        
        for stock in selected_stocks:
            sector = stock.get('sector', '未知')
            if sector not in sector_weights:
                sector_weights[sector] = 0
            sector_weights[sector] += 1 / total_weight
        
        # 检查是否有行业权重过高
        max_sector_weight = max(sector_weights.values()) if sector_weights else 0
        
        return {
            'sector_weights': sector_weights,
            'max_sector_weight': max_sector_weight,
            'concentration_risk': max_sector_weight > self.max_sector_weight
        }
    
    def _calculate_var_cvar(self, selected_stocks: List[Dict],
                          historical_data: Dict, confidence_level=0.95) -> Tuple[float, float]:
        """计算VaR和CVaR"""
        returns_data = self._prepare_returns_data(selected_stocks, historical_data)
        
        if returns_data.empty:
            return 0, 0
        
        # 等权重组合收益率
        portfolio_returns = returns_data.mean(axis=1)
        
        # VaR计算
        var_level = 1 - confidence_level
        var = portfolio_returns.quantile(var_level)
        
        # CVaR计算（条件VaR）
        cvar = portfolio_returns[portfolio_returns <= var].mean()
        
        return var, cvar
    
    def _prepare_returns_data(self, selected_stocks: List[Dict],
                            historical_data: Dict) -> pd.DataFrame:
        """准备收益率数据"""
        returns_data = pd.DataFrame()
        
        for stock in selected_stocks:
            code = stock['code']
            if code in historical_data:
                price_data = historical_data[code]
                returns = price_data['close'].pct_change().dropna()
                returns_data[code] = returns
        
        return returns_data.dropna()
    
    def _risk_parity_optimization(self, cov_matrix: np.ndarray) -> np.ndarray:
        """风险平价优化"""
        # 简化版风险平价：权重与波动率成反比
        volatilities = np.sqrt(np.diag(cov_matrix))
        inv_vol_weights = 1 / volatilities
        weights = inv_vol_weights / inv_vol_weights.sum()
        
        return weights
    
    def _classify_risk_level(self, volatility: float, max_drawdown: float) -> str:
        """风险等级分类"""
        if volatility > 0.4 or max_drawdown < -0.3:
            return "高风险"
        elif volatility > 0.25 or max_drawdown < -0.2:
            return "中等风险"
        else:
            return "低风险"
    
    def generate_risk_report(self, risk_metrics: Dict) -> str:
        """生成风险报告"""
        report = "🛡️ 投资组合风险分析报告\n"
        report += "=" * 40 + "\n\n"
        
        # 组合整体风险
        report += f"📊 组合整体风险:\n"
        report += f"   - 预期年化波动率: {risk_metrics['portfolio_volatility']:.2%}\n"
        report += f"   - 95% VaR: {risk_metrics['var_95']:.2%}\n"
        report += f"   - 95% CVaR: {risk_metrics['cvar_95']:.2%}\n"
        report += f"   - 预期最大回撤: {risk_metrics['max_drawdown_estimate']:.2%}\n"
        report += f"   - 综合风险评分: {risk_metrics['risk_score']:.1f}/100\n\n"
        
        # 行业集中度
        sector_info = risk_metrics['sector_concentration']
        report += f"🏭 行业分布:\n"
        for sector, weight in sector_info['sector_weights'].items():
            report += f"   - {sector}: {weight:.1%}\n"
        
        if sector_info['concentration_risk']:
            report += f"⚠️ 警告: 行业集中度过高!\n\n"
        
        # 风险建议
        report += self._generate_risk_suggestions(risk_metrics)
        
        return report 