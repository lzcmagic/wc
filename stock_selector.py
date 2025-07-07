"""
选股策略主模块
集成数据获取和技术指标分析，实现每日自动选股功能
"""

import pandas as pd
from datetime import datetime, timedelta
import time
import json
import os

from data_fetcher import StockDataFetcher
from indicators import StockScorer


class PersonalStockSelector:
    def __init__(self, config=None):
        self.fetcher = StockDataFetcher()
        self.scorer = StockScorer()
        self.config = config or self._default_config()
        
        # 创建结果存储目录
        if not os.path.exists('results'):
            os.makedirs('results')
    
    def _default_config(self):
        """默认配置"""
        return {
            'min_market_cap': 5000000000,  # 50亿
            'max_recent_gain': 30,         # 30%
            'min_score': 70,               # 最低评分
            'max_stocks': 10,              # 最多推荐股票数
            'analysis_period': 60          # 分析周期（天）
        }
    
    def filter_basic_criteria(self, stock_list):
        """基础筛选条件"""
        print("正在进行基础筛选...")
        filtered_stocks = []
        
        # 获取市场数据用于筛选
        try:
            market_data = self.fetcher.get_stock_list()
            if market_data.empty:
                print("无法获取股票列表")
                return []
            
            # 限制处理数量以避免API限制
            sample_size = min(100, len(market_data))
            sample_stocks = market_data.head(sample_size)
            
            for idx, (_, stock) in enumerate(sample_stocks.iterrows()):
                if idx % 10 == 0:
                    print(f"已处理 {idx}/{sample_size} 只股票...")
                
                stock_code = stock['code']
                stock_name = stock['name']
                
                # 过滤ST股票
                if 'ST' in stock_name or '*ST' in stock_name:
                    continue
                
                # 过滤退市风险股
                if '退' in stock_name:
                    continue
                
                # 获取市值信息
                market_info = self.fetcher.get_market_cap(stock_code)
                if market_info['circulation_market_cap'] < self.config['min_market_cap']:
                    continue
                
                # 获取近期涨幅
                recent_data = self.fetcher.get_stock_data(stock_code, 30)
                if recent_data.empty or len(recent_data) < 20:
                    continue
                
                recent_gain = (recent_data['close'].iloc[-1] / recent_data['close'].iloc[0] - 1) * 100
                if recent_gain > self.config['max_recent_gain']:
                    continue
                
                filtered_stocks.append({
                    'code': stock_code,
                    'name': stock_name,
                    'market_cap': market_info['circulation_market_cap'],
                    'recent_gain': recent_gain
                })
                
                # 避免请求过于频繁
                time.sleep(0.2)
                
                # 限制筛选数量
                if len(filtered_stocks) >= 50:
                    break
            
            print(f"基础筛选完成，符合条件的股票: {len(filtered_stocks)} 只")
            return filtered_stocks
            
        except Exception as e:
            print(f"基础筛选出错: {e}")
            return []
    
    def calculate_stock_scores(self, stock_list):
        """计算股票评分"""
        print("正在计算股票评分...")
        scored_stocks = []
        
        for idx, stock in enumerate(stock_list):
            print(f"正在分析 {stock['name']} ({stock['code']}) [{idx+1}/{len(stock_list)}]")
            
            try:
                # 获取历史数据
                stock_data = self.fetcher.get_stock_data(
                    stock['code'], 
                    self.config['analysis_period']
                )
                
                if stock_data.empty or len(stock_data) < 30:
                    print(f"  数据不足，跳过")
                    continue
                
                # 计算评分
                score = self.scorer.calculate_score(stock_data)
                
                if score >= self.config['min_score']:
                    # 获取信号原因
                    reasons = self.scorer.get_signal_reasons(stock_data)
                    
                    # 获取当前价格
                    current_price = stock_data['close'].iloc[-1]
                    
                    scored_stocks.append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'score': round(score, 1),
                        'current_price': round(current_price, 2),
                        'reasons': reasons,
                        'market_cap': stock['market_cap'],
                        'recent_gain': round(stock['recent_gain'], 2)
                    })
                    
                    print(f"  评分: {score:.1f}, 信号: {', '.join(reasons)}")
                else:
                    print(f"  评分: {score:.1f} (低于阈值)")
                    
            except Exception as e:
                print(f"  分析出错: {e}")
                continue
            
            # 避免请求过于频繁
            time.sleep(0.1)
        
        return scored_stocks
    
    def daily_stock_selection(self):
        """每日选股主函数"""
        print(f"开始执行每日选股 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        try:
            # 1. 获取股票列表并进行基础筛选
            stock_list = self.filter_basic_criteria([])
            
            if not stock_list:
                print("没有符合基础筛选条件的股票")
                return []
            
            # 2. 计算股票评分
            scored_stocks = self.calculate_stock_scores(stock_list)
            
            if not scored_stocks:
                print("没有符合评分要求的股票")
                return []
            
            # 3. 按评分排序
            top_stocks = sorted(
                scored_stocks, 
                key=lambda x: x['score'], 
                reverse=True
            )[:self.config['max_stocks']]
            
            # 4. 保存结果
            self.save_results(top_stocks)
            
            # 5. 输出结果
            self.print_results(top_stocks)
            
            print("=" * 50)
            print(f"选股完成，推荐 {len(top_stocks)} 只股票")
            
            return top_stocks
            
        except Exception as e:
            print(f"选股过程出错: {e}")
            return []
    
    def save_results(self, stocks):
        """保存选股结果"""
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"results/stock_selection_{today}.json"
        
        result_data = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'stocks': stocks,
            'summary': {
                'total_recommended': len(stocks),
                'avg_score': round(sum(s['score'] for s in stocks) / len(stocks), 1) if stocks else 0,
                'score_range': [min(s['score'] for s in stocks), max(s['score'] for s in stocks)] if stocks else [0, 0]
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            print(f"\n结果已保存到: {filename}")
        except Exception as e:
            print(f"保存结果失败: {e}")
    
    def print_results(self, stocks):
        """打印选股结果"""
        if not stocks:
            print("今日无推荐股票")
            return
        
        print(f"\n📈 今日选股推荐 - {datetime.now().strftime('%Y-%m-%d')}")
        print("=" * 60)
        
        for i, stock in enumerate(stocks, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            print(f"\n{medal} {stock['name']} ({stock['code']}) - 评分: {stock['score']}/100")
            print(f"   当前价格: ¥{stock['current_price']}")
            print(f"   市值: {stock['market_cap']/100000000:.0f}亿")
            print(f"   近30日涨幅: {stock['recent_gain']:+.1f}%")
            
            if stock['reasons']:
                print(f"   推荐理由: {' + '.join(stock['reasons'])}")
            else:
                print(f"   推荐理由: 综合技术指标良好")
        
        print("\n⚠️  风险提示:")
        print("   本推荐仅基于技术分析，不构成投资建议")
        print("   股市有风险，投资需谨慎，请结合基本面分析")
    
    def load_historical_results(self, date=None):
        """加载历史选股结果"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        filename = f"results/stock_selection_{date}.json"
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"未找到 {date} 的选股结果")
            return None
        except Exception as e:
            print(f"加载历史结果失败: {e}")
            return None
    
    def analyze_performance(self, days_back=7):
        """分析近期推荐股票的表现"""
        print(f"分析近 {days_back} 天推荐股票表现...")
        
        performance_data = []
        
        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            results = self.load_historical_results(date)
            
            if results:
                performance_data.append({
                    'date': date,
                    'stocks': results['stocks'],
                    'count': len(results['stocks']),
                    'avg_score': results['summary']['avg_score']
                })
        
        if performance_data:
            print(f"\n近 {len(performance_data)} 天推荐统计:")
            for data in performance_data:
                print(f"  {data['date']}: {data['count']}只股票, 平均评分: {data['avg_score']}")
        else:
            print("暂无历史数据")


# 快速测试脚本
def quick_test():
    """快速测试选股功能"""
    print("开始快速测试...")
    
    # 创建选股器
    selector = PersonalStockSelector({
        'min_market_cap': 3000000000,  # 降低到30亿便于测试
        'max_recent_gain': 50,         # 放宽到50%
        'min_score': 60,               # 降低到60分
        'max_stocks': 5,               # 只推荐5只
        'analysis_period': 40          # 减少到40天
    })
    
    # 手动指定几只知名股票进行测试
    test_stocks = [
        {'code': '000001', 'name': '平安银行', 'market_cap': 50000000000, 'recent_gain': 5},
        {'code': '000002', 'name': '万科A', 'market_cap': 80000000000, 'recent_gain': -2},
        {'code': '600036', 'name': '招商银行', 'market_cap': 120000000000, 'recent_gain': 3},
    ]
    
    print("正在分析测试股票...")
    scored_stocks = selector.calculate_stock_scores(test_stocks)
    
    if scored_stocks:
        selector.print_results(scored_stocks)
    else:
        print("测试股票均未达到推荐标准")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        quick_test()
    else:
        # 正常选股流程
        selector = PersonalStockSelector()
        results = selector.daily_stock_selection() 