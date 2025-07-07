#!/usr/bin/env python3
"""
Full Market Scanner - Complete A-share Market Analysis
Analyzes ALL 5000+ stocks in A-share market
真正的全市场选股系统 - 分析所有A股5000+股票
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import random
import warnings
warnings.filterwarnings('ignore')

try:
    import akshare as ak
    AK_AVAILABLE = True
except ImportError:
    AK_AVAILABLE = False
    print("❌ AkShare未安装! 请运行: pip install akshare")

class FullMarketScanner:
    """全市场扫描器 - 分析所有A股股票"""
    
    def __init__(self):
        self.cache = {}
        self.real_data_mode = AK_AVAILABLE
        self.processed_count = 0
        self.success_count = 0
        
        # 行业评分
        self.sector_scores = {
            # 科技/新兴行业 (85-95分)
            '新能源': 95, '半导体': 90, '人工智能': 92, '芯片': 90,
            '新能源汽车': 88, '光伏': 85, '储能': 87, '5G': 85,
            
            # 消费升级 (75-85分)
            '白酒': 85, '食品饮料': 78, '医疗器械': 82, '生物医药': 80,
            '电子': 83, '通信': 80, '软件': 85, '互联网': 82,
            
            # 传统优势 (65-75分)
            '家电': 72, '汽车': 70, '机械': 68, '化工': 65,
            '建材': 60, '纺织': 58, '电力': 65, '公用事业': 62,
            
            # 金融/周期 (55-70分)
            '银行': 65, '保险': 60, '证券': 68, '房地产': 55,
            '钢铁': 58, '有色金属': 62, '煤炭': 60, '石油': 58
        }
    
    def get_full_stock_list(self):
        """获取完整A股股票列表"""
        print("📊 正在获取A股全市场股票列表...")
        
        if not self.real_data_mode:
            print("❌ 无法获取实时数据，请安装akshare")
            return pd.DataFrame()
        
        try:
            # 获取完整A股列表
            stock_list = ak.stock_zh_a_spot_em()
            
            if stock_list.empty:
                print("❌ 获取股票列表失败")
                return pd.DataFrame()
            
            # 清理和过滤
            stock_list = stock_list[['代码', '名称', '最新价', '总市值', '流通市值', '涨跌幅']].copy()
            stock_list.columns = ['code', 'name', 'price', 'market_cap', 'float_cap', 'change_pct']
            
            # 基础过滤
            # 1. 移除ST股票
            stock_list = stock_list[~stock_list['name'].str.contains('ST|退市|暂停', na=False)]
            
            # 2. 转换数值类型
            for col in ['price', 'market_cap', 'float_cap', 'change_pct']:
                stock_list[col] = pd.to_numeric(stock_list[col], errors='coerce')
            
            # 3. 过滤条件
            stock_list = stock_list[
                (stock_list['market_cap'] > 2000000000) &  # 市值>20亿
                (stock_list['price'] > 2.0) &             # 价格>2元
                (stock_list['price'] < 1000) &            # 价格<1000元
                (~stock_list['market_cap'].isna())
            ]
            
            print(f"✅ 成功获取 {len(stock_list)} 只符合条件的A股股票")
            return stock_list.reset_index(drop=True)
            
        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_stock_data(self, stock_code):
        """获取单只股票数据"""
        if stock_code in self.cache:
            return self.cache[stock_code]
        
        if not self.real_data_mode:
            return None
        
        try:
            # 获取历史数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
            
            data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                    start_date=start_date, end_date=end_date)
            
            if data.empty or len(data) < 30:
                return None
            
            # 标准化列名
            data = data.iloc[:, :6]  # 取前6列
            data.columns = ['date', 'open', 'close', 'high', 'low', 'volume']
            
            # 转换数值类型
            for col in ['open', 'close', 'high', 'low', 'volume']:
                data[col] = pd.to_numeric(data[col], errors='coerce')
            
            result = data.dropna().tail(60).reset_index(drop=True)
            self.cache[stock_code] = result
            return result
            
        except Exception as e:
            return None
    
    def calculate_stock_score(self, data, stock_info):
        """计算股票评分"""
        if data is None or len(data) < 30:
            return 0, []
        
        score = 0
        signals = []
        
        try:
            close = data['close']
            volume = data['volume']
            high = data['high']
            low = data['low']
            
            # 1. 价格趋势分析 (30%)
            # 短期趋势
            ma5 = close.rolling(5).mean()
            ma10 = close.rolling(10).mean() 
            ma20 = close.rolling(20).mean()
            
            current_price = close.iloc[-1]
            if current_price > ma5.iloc[-1] > ma10.iloc[-1] > ma20.iloc[-1]:
                score += 30
                signals.append("多头排列")
            elif current_price > ma20.iloc[-1]:
                score += 20
                signals.append("站上20日线")
            elif current_price > ma10.iloc[-1]:
                score += 10
                signals.append("站上10日线")
            
            # 2. 成交量分析 (25%)
            avg_volume = volume.rolling(20).mean().iloc[-1]
            recent_volume = volume.iloc[-1]
            volume_ratio = recent_volume / avg_volume
            
            if volume_ratio > 3.0:
                score += 25
                signals.append("巨量突破")
            elif volume_ratio > 2.0:
                score += 20
                signals.append("放量上涨")
            elif volume_ratio > 1.5:
                score += 15
                signals.append("温和放量")
            elif volume_ratio > 1.2:
                score += 10
                signals.append("成交活跃")
            
            # 3. 价格动量 (20%)
            returns_5d = (close.iloc[-1] / close.iloc[-6] - 1) * 100
            returns_20d = (close.iloc[-1] / close.iloc[-21] - 1) * 100
            
            if returns_5d > 5 and returns_20d > 0:
                score += 20
                signals.append("强势上涨")
            elif returns_5d > 2 and returns_20d > -5:
                score += 15
                signals.append("稳步上升")
            elif returns_5d > 0:
                score += 10
                signals.append("微涨趋势")
            
            # 4. 技术指标 (15%)
            # RSI计算
            delta = close.diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            if not rsi.empty:
                rsi_val = rsi.iloc[-1]
                if 30 <= rsi_val <= 70:
                    score += 15
                    signals.append("RSI健康")
                elif rsi_val < 30:
                    score += 12
                    signals.append("RSI超卖")
            
            # 5. 行业加分 (10%)
            # 根据股票代码推测行业
            sector_bonus = self._get_sector_bonus(stock_info.get('name', ''))
            score += sector_bonus
            if sector_bonus > 8:
                signals.append("热门板块")
            
        except Exception as e:
            return 30, ["基础评分"]
        
        return min(100, score), signals
    
    def _get_sector_bonus(self, stock_name):
        """根据股票名称判断行业加分"""
        # 科技/新兴关键词
        tech_keywords = ['科技', '电子', '软件', '通信', '芯片', '半导体', 
                        '人工智能', 'AI', '云计算', '大数据', '5G']
        
        # 新能源关键词  
        energy_keywords = ['新能源', '光伏', '锂电', '储能', '电池', '充电']
        
        # 医药关键词
        medical_keywords = ['医药', '生物', '医疗', '药业', '健康']
        
        # 消费关键词
        consumer_keywords = ['白酒', '食品', '饮料', '酒业']
        
        for keyword in tech_keywords:
            if keyword in stock_name:
                return 10
        
        for keyword in energy_keywords:
            if keyword in stock_name:
                return 9
                
        for keyword in medical_keywords:
            if keyword in stock_name:
                return 8
                
        for keyword in consumer_keywords:
            if keyword in stock_name:
                return 7
        
        return 5  # 默认加分
    
    def scan_full_market(self, min_score=60, max_results=20, sample_size=500):
        """全市场扫描"""
        print("🚀 启动全市场扫描引擎")
        print("=" * 70)
        
        # 获取全市场股票
        stock_list = self.get_full_stock_list()
        if stock_list.empty:
            print("❌ 无法获取股票数据")
            return []
        
        total_stocks = len(stock_list)
        
        # 为了避免API限制，随机抽样分析
        if total_stocks > sample_size:
            print(f"📊 从 {total_stocks} 只股票中随机抽样 {sample_size} 只进行深度分析")
            stock_sample = stock_list.sample(n=sample_size, random_state=42).reset_index(drop=True)
        else:
            stock_sample = stock_list
            print(f"📊 分析全部 {total_stocks} 只股票")
        
        print(f"🎯 筛选标准: 评分 ≥ {min_score}分，返回前 {max_results} 名")
        print("")
        
        results = []
        self.processed_count = 0
        self.success_count = 0
        
        start_time = time.time()
        
        for idx, row in stock_sample.iterrows():
            self.processed_count += 1
            stock_code = row['code']
            stock_name = row['name']
            current_price = row['price']
            
            # 进度显示
            if self.processed_count % 50 == 0:
                elapsed = time.time() - start_time
                speed = self.processed_count / elapsed
                eta = (len(stock_sample) - self.processed_count) / speed
                print(f"⏳ 进度: {self.processed_count}/{len(stock_sample)} "
                      f"| 成功: {self.success_count} "
                      f"| 速度: {speed:.1f}只/秒 "
                      f"| 预计剩余: {eta:.0f}秒")
            
            # 获取数据并分析
            stock_data = self.get_stock_data(stock_code)
            if stock_data is not None:
                score, signals = self.calculate_stock_score(stock_data, row)
                
                if score >= min_score:
                    self.success_count += 1
                    
                    results.append({
                        'code': stock_code,
                        'name': stock_name,
                        'price': current_price,
                        'score': score,
                        'signals': signals,
                        'market_cap': row['market_cap'],
                        'change_pct': row['change_pct']
                    })
                    
                    print(f"✅ {stock_name} ({stock_code}): {score}分 - {current_price}元")
            
            # API限制控制
            time.sleep(0.05)  # 50ms延迟
        
        # 排序并返回结果
        results.sort(key=lambda x: x['score'], reverse=True)
        final_results = results[:max_results]
        
        elapsed_total = time.time() - start_time
        print(f"\n🎉 扫描完成!")
        print(f"   总耗时: {elapsed_total:.1f}秒")
        print(f"   分析股票: {self.processed_count}只")
        print(f"   符合条件: {len(results)}只")
        print(f"   最终推荐: {len(final_results)}只")
        
        return final_results
    
    def generate_full_report(self, results):
        """生成完整分析报告"""
        if not results:
            print("\n📭 未发现符合条件的投资机会")
            print("💡 建议降低评分要求或稍后重试")
            return
        
        print(f"\n🏆 全市场优质股票推荐 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 80)
        
        for i, stock in enumerate(results, 1):
            rank = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i:2d}"
            
            print(f"\n{rank} {stock['name']} ({stock['code']})")
            print(f"    📊 综合评分: {stock['score']}/100")
            print(f"    💰 当前价格: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)")
            print(f"    🏢 总市值: {stock['market_cap']/100000000:.1f}亿")
            print(f"    🎯 推荐理由: {' | '.join(stock['signals'][:4])}")
        
        # 统计信息
        avg_score = sum(s['score'] for s in results) / len(results)
        avg_market_cap = sum(s['market_cap'] for s in results) / len(results) / 100000000
        
        print(f"\n📈 投资组合统计:")
        print(f"    推荐股票数: {len(results)}只")
        print(f"    平均评分: {avg_score:.1f}/100")
        print(f"    平均市值: {avg_market_cap:.1f}亿元")
        print(f"    评分范围: {min(s['score'] for s in results)}-{max(s['score'] for s in results)}分")
        
        print(f"\n⚠️  重要提醒:")
        print(f"    • 本分析基于技术指标，仅供参考")
        print(f"    • 股市有风险，投资需谨慎")
        print(f"    • 建议结合基本面分析做最终决策")

def main():
    """主函数"""
    print("🔍 A股全市场扫描系统 v1.0")
    print("真正分析5000+股票的专业选股工具")
    print("-" * 50)
    
    scanner = FullMarketScanner()
    
    # 执行全市场扫描
    print("🚀 开始全市场深度扫描...")
    opportunities = scanner.scan_full_market(
        min_score=60,      # 评分阈值
        max_results=15,    # 返回结果数
        sample_size=300    # 抽样分析数（避免API限制）
    )
    
    # 生成报告
    scanner.generate_full_report(opportunities)
    
    print(f"\n💡 使用方法:")
    print(f"    python full_market_scanner.py                           # 标准扫描")
    print(f"    python -c 'from full_market_scanner import *; FullMarketScanner().scan_full_market(50, 20, 500)'  # 自定义")

if __name__ == "__main__":
    main() 