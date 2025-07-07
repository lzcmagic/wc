#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
行业轮动分析系统 - 智能板块分析器
支持热点识别、板块强度分析、轮动预测、资金流向追踪
"""

import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any, Tuple, Optional
import json
import os
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SectorInfo:
    """行业信息类"""
    code: str
    name: str
    stocks_count: int
    total_market_cap: float
    avg_pe: float
    avg_pb: float
    turnover_rate: float

@dataclass
class SectorPerformance:
    """行业表现类"""
    sector_code: str
    sector_name: str
    change_1d: float
    change_3d: float
    change_5d: float
    change_10d: float
    change_20d: float
    volume_ratio: float
    money_flow: float
    strength_score: float
    trend_score: float
    momentum_score: float
    overall_score: float
    rank: int
    status: str  # 热门、温和、冷门

class SectorRotationAnalyzer:
    """行业轮动分析器"""
    
    def __init__(self):
        self.sectors_data = {}
        self.historical_data = {}
        self.rotation_patterns = {}
        
        # 确保数据目录存在
        os.makedirs('sector_data', exist_ok=True)
        
        # 初始化行业映射
        self.init_sector_mapping()
    
    def init_sector_mapping(self):
        """初始化行业分类映射"""
        self.sector_mapping = {
            # 主要行业分类
            'BK0420': '房地产',
            'BK0421': '银行',
            'BK0422': '保险',
            'BK0423': '证券',
            'BK0424': '酿酒',
            'BK0425': '汽车',
            'BK0426': '钢铁',
            'BK0427': '煤炭',
            'BK0428': '有色金属',
            'BK0429': '石油化工',
            'BK0430': '电力',
            'BK0431': '电子',
            'BK0432': '计算机',
            'BK0433': '通信',
            'BK0434': '医药生物',
            'BK0435': '食品饮料',
            'BK0436': '纺织服装',
            'BK0437': '轻工制造',
            'BK0438': '商业贸易',
            'BK0439': '交通运输',
            'BK0440': '机械设备',
            'BK0441': '建筑材料',
            'BK0442': '建筑装饰',
            'BK0443': '公用事业',
            'BK0444': '农林牧渔',
            'BK0445': '综合',
            'BK0446': '化工',
            'BK0447': '传媒',
            'BK0448': '国防军工',
            'BK0449': '家用电器',
            'BK0450': '休闲服务',
            'BK0451': '环保',
            'BK0452': '新能源',
            'BK0453': '人工智能',
            'BK0454': '5G概念',
            'BK0455': '芯片',
            'BK0456': '新材料',
            'BK0457': '生物医药'
        }
        
        # 概念板块映射
        self.concept_mapping = {
            'BK0900': '新能源汽车',
            'BK0901': '锂电池',
            'BK0902': '光伏',
            'BK0903': '风电',
            'BK0904': '储能',
            'BK0905': '氢能源',
            'BK0906': '充电桩',
            'BK0907': '智能驾驶',
            'BK0908': '车联网',
            'BK0909': '新基建',
            'BK0910': '数字货币',
            'BK0911': '区块链',
            'BK0912': '量子通信',
            'BK0913': '工业互联网',
            'BK0914': '物联网',
            'BK0915': '云计算',
            'BK0916': '大数据',
            'BK0917': '边缘计算',
            'BK0918': '网络安全',
            'BK0919': '虚拟现实',
            'BK0920': 'AI芯片'
        }
    
    def get_sector_stocks(self, sector_code: str) -> List[Dict]:
        """获取行业股票列表"""
        try:
            # 获取行业股票
            if sector_code.startswith('BK'):
                # 同花顺行业分类
                df = ak.stock_board_industry_cons_ths(symbol=sector_code)
            else:
                # 其他分类方式
                df = ak.stock_sector_detail(sector=sector_code)
            
            if df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': row.get('代码', row.get('code', '')),
                    'name': row.get('名称', row.get('name', '')),
                    'sector_code': sector_code
                })
            
            return stocks
        
        except Exception as e:
            logger.error(f"获取行业股票失败 {sector_code}: {e}")
            return []
    
    def get_sector_market_data(self, sector_code: str) -> Optional[pd.DataFrame]:
        """获取行业市场数据"""
        try:
            # 获取行业指数数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
            
            # 尝试获取同花顺行业指数
            df = ak.stock_board_industry_hist_ths(
                symbol=sector_code,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if df.empty:
                return None
            
            # 重命名列
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount', 'change_pct']
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            return df
        
        except Exception as e:
            logger.error(f"获取行业数据失败 {sector_code}: {e}")
            return None
    
    def calculate_sector_performance(self, sector_code: str, sector_name: str) -> Optional[SectorPerformance]:
        """计算行业表现指标"""
        try:
            df = self.get_sector_market_data(sector_code)
            if df is None or len(df) < 20:
                return None
            
            # 计算各期涨跌幅
            latest_price = df['close'].iloc[-1]
            
            # 1日涨跌幅
            change_1d = df['change_pct'].iloc[-1] if len(df) >= 1 else 0
            
            # 3日涨跌幅
            if len(df) >= 3:
                price_3d_ago = df['close'].iloc[-3]
                change_3d = (latest_price - price_3d_ago) / price_3d_ago * 100
            else:
                change_3d = 0
            
            # 5日涨跌幅
            if len(df) >= 5:
                price_5d_ago = df['close'].iloc[-5]
                change_5d = (latest_price - price_5d_ago) / price_5d_ago * 100
            else:
                change_5d = 0
            
            # 10日涨跌幅
            if len(df) >= 10:
                price_10d_ago = df['close'].iloc[-10]
                change_10d = (latest_price - price_10d_ago) / price_10d_ago * 100
            else:
                change_10d = 0
            
            # 20日涨跌幅
            if len(df) >= 20:
                price_20d_ago = df['close'].iloc[-20]
                change_20d = (latest_price - price_20d_ago) / price_20d_ago * 100
            else:
                change_20d = 0
            
            # 计算成交量比率
            recent_volume = df['volume'].iloc[-5:].mean()
            previous_volume = df['volume'].iloc[-15:-5].mean()
            volume_ratio = recent_volume / previous_volume if previous_volume > 0 else 1
            
            # 计算资金流向（简化版）
            money_flow = df['amount'].iloc[-5:].sum() / df['amount'].iloc[-15:-5].sum() if len(df) >= 15 else 1
            
            # 计算强度评分
            strength_score = self._calculate_strength_score(change_1d, change_3d, change_5d, volume_ratio)
            
            # 计算趋势评分
            trend_score = self._calculate_trend_score(change_5d, change_10d, change_20d)
            
            # 计算动量评分
            momentum_score = self._calculate_momentum_score(change_1d, change_3d, volume_ratio)
            
            # 综合评分
            overall_score = (strength_score * 0.4 + trend_score * 0.3 + momentum_score * 0.3)
            
            # 判断状态
            if overall_score >= 75:
                status = "热门"
            elif overall_score >= 55:
                status = "温和"
            else:
                status = "冷门"
            
            return SectorPerformance(
                sector_code=sector_code,
                sector_name=sector_name,
                change_1d=change_1d,
                change_3d=change_3d,
                change_5d=change_5d,
                change_10d=change_10d,
                change_20d=change_20d,
                volume_ratio=volume_ratio,
                money_flow=money_flow,
                strength_score=strength_score,
                trend_score=trend_score,
                momentum_score=momentum_score,
                overall_score=overall_score,
                rank=0,  # 后续排序时填充
                status=status
            )
        
        except Exception as e:
            logger.error(f"计算行业表现失败 {sector_code}: {e}")
            return None
    
    def _calculate_strength_score(self, change_1d: float, change_3d: float, 
                                 change_5d: float, volume_ratio: float) -> float:
        """计算强度评分"""
        # 涨跌幅评分
        price_score = 0
        if change_1d > 5:
            price_score += 40
        elif change_1d > 2:
            price_score += 30
        elif change_1d > 0:
            price_score += 20
        elif change_1d > -2:
            price_score += 10
        
        if change_3d > 10:
            price_score += 30
        elif change_3d > 5:
            price_score += 20
        elif change_3d > 0:
            price_score += 10
        
        if change_5d > 15:
            price_score += 30
        elif change_5d > 8:
            price_score += 20
        elif change_5d > 0:
            price_score += 10
        
        # 成交量评分
        volume_score = 0
        if volume_ratio > 2:
            volume_score = 30
        elif volume_ratio > 1.5:
            volume_score = 20
        elif volume_ratio > 1.2:
            volume_score = 15
        elif volume_ratio > 1:
            volume_score = 10
        
        return min(100, price_score + volume_score)
    
    def _calculate_trend_score(self, change_5d: float, change_10d: float, change_20d: float) -> float:
        """计算趋势评分"""
        score = 50  # 基础分
        
        # 短期趋势
        if change_5d > 10:
            score += 20
        elif change_5d > 5:
            score += 15
        elif change_5d > 0:
            score += 10
        elif change_5d < -10:
            score -= 20
        elif change_5d < -5:
            score -= 15
        
        # 中期趋势
        if change_10d > 15:
            score += 15
        elif change_10d > 8:
            score += 10
        elif change_10d > 0:
            score += 5
        elif change_10d < -15:
            score -= 15
        elif change_10d < -8:
            score -= 10
        
        # 长期趋势
        if change_20d > 20:
            score += 15
        elif change_20d > 10:
            score += 10
        elif change_20d > 0:
            score += 5
        elif change_20d < -20:
            score -= 15
        elif change_20d < -10:
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_momentum_score(self, change_1d: float, change_3d: float, volume_ratio: float) -> float:
        """计算动量评分"""
        score = 50  # 基础分
        
        # 短期动量
        if change_1d > 3 and change_3d > 5:
            score += 25
        elif change_1d > 1 and change_3d > 2:
            score += 15
        elif change_1d > 0 and change_3d > 0:
            score += 10
        elif change_1d < -3 and change_3d < -5:
            score -= 25
        elif change_1d < -1 and change_3d < -2:
            score -= 15
        
        # 成交量动量
        if volume_ratio > 1.8:
            score += 25
        elif volume_ratio > 1.4:
            score += 15
        elif volume_ratio > 1.1:
            score += 10
        elif volume_ratio < 0.8:
            score -= 15
        
        return max(0, min(100, score))
    
    def analyze_all_sectors(self) -> List[SectorPerformance]:
        """分析所有行业表现"""
        logger.info("开始分析所有行业表现...")
        
        performances = []
        
        # 分析主要行业
        for sector_code, sector_name in self.sector_mapping.items():
            logger.info(f"分析行业: {sector_name}")
            performance = self.calculate_sector_performance(sector_code, sector_name)
            if performance:
                performances.append(performance)
        
        # 分析概念板块
        for sector_code, sector_name in self.concept_mapping.items():
            logger.info(f"分析概念: {sector_name}")
            performance = self.calculate_sector_performance(sector_code, sector_name)
            if performance:
                performances.append(performance)
        
        # 按综合评分排序
        performances.sort(key=lambda x: x.overall_score, reverse=True)
        
        # 设置排名
        for i, performance in enumerate(performances, 1):
            performance.rank = i
        
        logger.info(f"完成分析，共 {len(performances)} 个行业/概念")
        return performances
    
    def identify_rotation_opportunities(self, performances: List[SectorPerformance]) -> Dict[str, List[SectorPerformance]]:
        """识别轮动机会"""
        
        # 分类板块
        hot_sectors = [p for p in performances if p.status == "热门"]
        warm_sectors = [p for p in performances if p.status == "温和"]
        cold_sectors = [p for p in performances if p.status == "冷门"]
        
        # 识别强势板块（近期表现好）
        rising_stars = [p for p in performances if p.change_5d > 8 and p.volume_ratio > 1.3]
        
        # 识别超跌反弹机会
        oversold_bounce = [p for p in performances if p.change_20d < -15 and p.change_3d > 0]
        
        # 识别破位下跌风险
        breakdown_risk = [p for p in performances if p.change_5d < -8 and p.volume_ratio > 1.5]
        
        # 识别稳健增长板块
        steady_growth = [p for p in performances if 
                        p.change_20d > 5 and p.change_20d < 20 and 
                        p.change_5d > 0 and p.change_5d < 10]
        
        return {
            "热门板块": hot_sectors[:10],
            "新兴强势": rising_stars[:8],
            "超跌反弹": oversold_bounce[:6],
            "破位风险": breakdown_risk[:5],
            "稳健增长": steady_growth[:8],
            "全部温和": warm_sectors,
            "全部冷门": cold_sectors
        }
    
    def generate_rotation_signals(self, performances: List[SectorPerformance]) -> Dict[str, Any]:
        """生成轮动信号"""
        
        if not performances:
            return {"signal": "无数据", "confidence": 0}
        
        # 分析市场整体情况
        avg_change_1d = np.mean([p.change_1d for p in performances])
        avg_change_5d = np.mean([p.change_5d for p in performances])
        avg_volume_ratio = np.mean([p.volume_ratio for p in performances])
        
        # 分析板块分化程度
        change_1d_std = np.std([p.change_1d for p in performances])
        
        # 生成市场信号
        market_signal = ""
        confidence = 50
        
        if avg_change_1d > 2 and avg_volume_ratio > 1.3:
            market_signal = "全面上涨"
            confidence = 85
        elif avg_change_1d > 1 and change_1d_std > 2:
            market_signal = "板块轮动"
            confidence = 75
        elif avg_change_1d < -2 and avg_volume_ratio > 1.2:
            market_signal = "全面下跌"
            confidence = 80
        elif change_1d_std < 1:
            market_signal = "市场平淡"
            confidence = 60
        else:
            market_signal = "震荡分化"
            confidence = 65
        
        # 推荐策略
        if market_signal == "全面上涨":
            strategy = "追涨强势板块，重点关注龙头股"
        elif market_signal == "板块轮动":
            strategy = "精选强势板块，回避弱势板块"
        elif market_signal == "全面下跌":
            strategy = "控制仓位，关注超跌反弹机会"
        elif market_signal == "震荡分化":
            strategy = "均衡配置，适度轮动"
        else:
            strategy = "耐心等待，关注变化信号"
        
        return {
            "market_signal": market_signal,
            "confidence": confidence,
            "strategy": strategy,
            "market_stats": {
                "avg_change_1d": round(avg_change_1d, 2),
                "avg_change_5d": round(avg_change_5d, 2),
                "avg_volume_ratio": round(avg_volume_ratio, 2),
                "divergence": round(change_1d_std, 2)
            }
        }
    
    def generate_sector_report(self, performances: List[SectorPerformance]) -> str:
        """生成行业轮动报告"""
        
        if not performances:
            return "暂无数据生成报告"
        
        # 获取轮动机会
        opportunities = self.identify_rotation_opportunities(performances)
        
        # 获取轮动信号
        signals = self.generate_rotation_signals(performances)
        
        report = f"""
🔄 行业轮动分析报告
{'='*60}
📅 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
📊 分析板块: {len(performances)} 个行业/概念

🎯 市场信号: {signals['market_signal']} (置信度: {signals['confidence']}%)
💡 操作策略: {signals['strategy']}

📈 市场统计:
   • 平均日涨幅: {signals['market_stats']['avg_change_1d']}%
   • 平均5日涨幅: {signals['market_stats']['avg_change_5d']}%
   • 平均量比: {signals['market_stats']['avg_volume_ratio']:.2f}
   • 板块分化度: {signals['market_stats']['divergence']:.2f}

🔥 热门板块 TOP5:
"""
        
        for i, sector in enumerate(opportunities["热门板块"][:5], 1):
            report += f"   {i}. {sector.sector_name} - {sector.change_1d:+.2f}% (评分: {sector.overall_score:.0f})\n"
        
        report += "\n⭐ 新兴强势板块:"
        for sector in opportunities["新兴强势"][:5]:
            report += f"\n   • {sector.sector_name}: 5日+{sector.change_5d:.1f}%, 量比{sector.volume_ratio:.1f}"
        
        if opportunities["超跌反弹"]:
            report += "\n\n🚀 超跌反弹机会:"
            for sector in opportunities["超跌反弹"][:3]:
                report += f"\n   • {sector.sector_name}: 20日{sector.change_20d:.1f}%, 近3日+{sector.change_3d:.1f}%"
        
        if opportunities["破位风险"]:
            report += "\n\n⚠️ 破位风险警示:"
            for sector in opportunities["破位风险"][:3]:
                report += f"\n   • {sector.sector_name}: 5日{sector.change_5d:.1f}%, 量比{sector.volume_ratio:.1f}"
        
        report += "\n\n📋 综合排行榜 TOP10:"
        for i, sector in enumerate(performances[:10], 1):
            status_emoji = "🔥" if sector.status == "热门" else "📈" if sector.status == "温和" else "📉"
            report += f"\n   {i:2d}. {status_emoji} {sector.sector_name:<12} {sector.change_1d:+6.2f}% (评分: {sector.overall_score:4.0f})"
        
        report += f"\n\n💼 投资建议:"
        report += f"\n   • 强势板块: 关注{opportunities['热门板块'][0].sector_name}、{opportunities['热门板块'][1].sector_name if len(opportunities['热门板块']) > 1 else '暂无'}"
        report += f"\n   • 成长机会: 关注{opportunities['新兴强势'][0].sector_name if opportunities['新兴强势'] else '暂无'}"
        if opportunities["超跌反弹"]:
            report += f"\n   • 反弹标的: 关注{opportunities['超跌反弹'][0].sector_name}"
        if opportunities["破位风险"]:
            report += f"\n   • 风险规避: 远离{opportunities['破位风险'][0].sector_name}"
        
        report += "\n\n⚠️ 风险提示:"
        report += "\n   • 板块轮动分析仅供参考，不构成投资建议"
        report += "\n   • 市场变化快速，请结合实时情况调整策略"
        report += "\n   • 注意控制仓位，分散投资风险"
        
        return report
    
    def save_analysis_result(self, performances: List[SectorPerformance], filename: str = None):
        """保存分析结果"""
        if filename is None:
            filename = f"sector_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join('sector_data', filename)
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'total_sectors': len(performances),
            'performances': [
                {
                    'sector_code': p.sector_code,
                    'sector_name': p.sector_name,
                    'change_1d': p.change_1d,
                    'change_3d': p.change_3d,
                    'change_5d': p.change_5d,
                    'change_10d': p.change_10d,
                    'change_20d': p.change_20d,
                    'volume_ratio': p.volume_ratio,
                    'money_flow': p.money_flow,
                    'strength_score': p.strength_score,
                    'trend_score': p.trend_score,
                    'momentum_score': p.momentum_score,
                    'overall_score': p.overall_score,
                    'rank': p.rank,
                    'status': p.status
                }
                for p in performances
            ]
        }
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"分析结果已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存分析结果失败: {e}")

def main():
    """主程序"""
    print("🔄 行业轮动分析系统")
    print("="*50)
    
    analyzer = SectorRotationAnalyzer()
    
    while True:
        print("\n请选择功能:")
        print("1. 🔍 分析所有行业")
        print("2. 📊 生成轮动报告")
        print("3. 🎯 查看轮动机会")
        print("4. 📈 单个行业分析")
        print("5. 💾 保存分析结果")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-5): ").strip()
        
        if choice == "1":
            print("🔍 正在分析所有行业...")
            performances = analyzer.analyze_all_sectors()
            
            if performances:
                print(f"\n✅ 分析完成! 共分析 {len(performances)} 个行业/概念")
                print(f"热门板块: {len([p for p in performances if p.status == '热门'])} 个")
                print(f"温和板块: {len([p for p in performances if p.status == '温和'])} 个")
                print(f"冷门板块: {len([p for p in performances if p.status == '冷门'])} 个")
                
                # 显示TOP5
                print("\n🏆 TOP5 强势板块:")
                for i, p in enumerate(performances[:5], 1):
                    print(f"   {i}. {p.sector_name} - 评分: {p.overall_score:.0f} ({p.status})")
            else:
                print("❌ 分析失败，请检查网络连接")
        
        elif choice == "2":
            print("📊 正在生成轮动报告...")
            performances = analyzer.analyze_all_sectors()
            
            if performances:
                report = analyzer.generate_sector_report(performances)
                print(report)
                
                # 询问是否保存报告
                save_choice = input("\n是否保存报告到文件? (y/n): ").lower()
                if save_choice == 'y':
                    filename = f"sector_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report)
                    print(f"✅ 报告已保存: {filename}")
            else:
                print("❌ 生成报告失败")
        
        elif choice == "3":
            print("🎯 正在识别轮动机会...")
            performances = analyzer.analyze_all_sectors()
            
            if performances:
                opportunities = analyzer.identify_rotation_opportunities(performances)
                
                for category, sectors in opportunities.items():
                    if sectors and category not in ["全部温和", "全部冷门"]:
                        print(f"\n{category}:")
                        for sector in sectors[:5]:  # 只显示前5个
                            print(f"   • {sector.sector_name} - {sector.change_1d:+.2f}% (评分: {sector.overall_score:.0f})")
            else:
                print("❌ 分析失败")
        
        elif choice == "0":
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 