"""
增强版A股选股系统 - 集成所有优化功能
包含技术面、基本面、资金面、行业面四维分析
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import os

try:
    import akshare as ak
except ImportError:
    print("AkShare未安装，请运行: pip install akshare")
    ak = None

from indicators import TechnicalIndicators

class EnhancedTechnicalIndicators:
    """增强版技术指标"""
    
    @staticmethod
    def calculate_atr(high, low, close, period=14):
        """计算真实波动范围 (ATR)"""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        
        ranges = pd.DataFrame({
            'hl': high_low,
            'hc': high_close,
            'lc': low_close
        })
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    
    @staticmethod
    def calculate_adx(high, low, close, period=14):
        """计算平均趋向指数 (ADX) - 趋势强度指标"""
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        atr = EnhancedTechnicalIndicators.calculate_atr(high, low, close, period)
        
        plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=period).mean()
        
        return adx.fillna(0), plus_di.fillna(0), minus_di.fillna(0)
    
    @staticmethod
    def calculate_williams_r(high, low, close, period=14):
        """计算威廉指标 %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        wr = -100 * (highest_high - close) / (highest_high - lowest_low)
        return wr.fillna(-50)
    
    @staticmethod
    def calculate_obv(close, volume):
        """计算能量潮指标 (OBV)"""
        obv_values = []
        obv = 0
        
        for i in range(len(close)):
            if i == 0:
                obv_values.append(volume.iloc[i])
            else:
                if close.iloc[i] > close.iloc[i-1]:
                    obv += volume.iloc[i]
                elif close.iloc[i] < close.iloc[i-1]:
                    obv -= volume.iloc[i]
                obv_values.append(obv)
        
        return pd.Series(obv_values, index=close.index)
    
    @staticmethod
    def calculate_roc(close, period=12):
        """计算变动率指标 (ROC)"""
        roc = (close / close.shift(period) - 1) * 100
        return roc.fillna(0)

class FundamentalAnalyzer:
    """基本面分析器"""
    
    def __init__(self):
        self.cache = {}
    
    def get_financial_data(self, stock_code):
        """获取财务数据"""
        if stock_code in self.cache:
            return self.cache[stock_code]
        
        if not ak:
            return self._get_default_financial_data()
        
        try:
            # 获取基本信息
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            
            result = {
                'pe_ratio': None,
                'pb_ratio': None,
                'roe': None,
                'total_market_cap': None,
                'revenue_growth': None
            }
            
            if not stock_info.empty:
                for _, row in stock_info.iterrows():
                    item = row['item']
                    value = str(row['value'])
                    
                    try:
                        if 'PE' in item or '市盈率' in item:
                            result['pe_ratio'] = float(value.replace(',', ''))
                        elif 'PB' in item or '市净率' in item:
                            result['pb_ratio'] = float(value.replace(',', ''))
                        elif '总市值' in item:
                            result['total_market_cap'] = float(value.replace(',', ''))
                        elif 'ROE' in item or '净资产收益率' in item:
                            result['roe'] = float(value.replace('%', '').replace(',', ''))
                    except (ValueError, AttributeError):
                        continue
            
            self.cache[stock_code] = result
            return result
            
        except Exception as e:
            print(f"获取 {stock_code} 财务数据失败: {e}")
            return self._get_default_financial_data()
    
    def _get_default_financial_data(self):
        """默认财务数据（当无法获取真实数据时）"""
        return {
            'pe_ratio': 20.0,
            'pb_ratio': 2.5,
            'roe': 10.0,
            'total_market_cap': 10000000000,
            'revenue_growth': 5.0
        }
    
    def score_fundamentals(self, financial_data):
        """基本面评分 (0-100分)"""
        score = 0
        reasons = []
        
        # PE估值评分 (0-30分)
        pe = financial_data.get('pe_ratio')
        if pe:
            if 8 <= pe <= 25:
                score += 30
                reasons.append("PE估值合理")
            elif 25 < pe <= 35:
                score += 20
                reasons.append("PE估值偏高但可接受")
            elif pe < 8:
                score += 25
                reasons.append("PE估值偏低")
            elif pe > 50:
                score -= 10
                reasons.append("PE估值过高")
        
        # PB估值评分 (0-25分)
        pb = financial_data.get('pb_ratio')
        if pb:
            if 1 <= pb <= 3:
                score += 25
                reasons.append("PB估值合理")
            elif pb < 1:
                score += 30
                reasons.append("PB估值偏低")
            elif pb > 5:
                score -= 5
                reasons.append("PB估值偏高")
        
        # ROE盈利能力评分 (0-35分)
        roe = financial_data.get('roe')
        if roe:
            if roe >= 15:
                score += 35
                reasons.append("ROE优秀")
            elif roe >= 10:
                score += 25
                reasons.append("ROE良好")
            elif roe >= 5:
                score += 15
                reasons.append("ROE一般")
            else:
                score -= 10
                reasons.append("ROE较差")
        
        # 市值规模评分 (0-10分)
        market_cap = financial_data.get('total_market_cap')
        if market_cap:
            if market_cap >= 50000000000:  # 500亿以上
                score += 10
                reasons.append("大盘股")
            elif market_cap >= 10000000000:  # 100亿以上
                score += 8
                reasons.append("中盘股")
        
        return min(100, max(0, score)), reasons

class MarketSentimentAnalyzer:
    """市场情绪分析器"""
    
    @staticmethod
    def calculate_price_momentum(close, period=20):
        """计算价格动量"""
        momentum = (close / close.shift(period) - 1) * 100
        return momentum.fillna(0)
    
    @staticmethod
    def calculate_volume_momentum(volume, period=20):
        """计算成交量动量"""
        avg_volume = volume.rolling(window=period).mean()
        volume_ratio = volume / avg_volume
        return volume_ratio.fillna(1)
    
    @staticmethod
    def calculate_volatility_score(close, period=20):
        """计算波动率评分（低波动率高分）"""
        returns = close.pct_change()
        volatility = returns.rolling(window=period).std()
        
        # 计算波动率百分位数
        volatility_percentile = volatility.rolling(window=60).rank(pct=True)
        # 反转评分：低波动率给高分
        score = (1 - volatility_percentile.fillna(0.5)) * 100
        return score

class IndustryAnalyzer:
    """行业分析器"""
    
    def __init__(self):
        # 定义行业强度评分
        self.industry_scores = {
            # 新兴行业 (高分)
            '新能源': 85, '半导体': 80, '人工智能': 85, '生物医药': 80,
            '新能源汽车': 85, '光伏': 80, '风电': 75, '储能': 80,
            '芯片': 80, '5G': 75, '云计算': 80, '大数据': 75,
            
            # 稳定行业 (中分)
            '白酒': 70, '食品饮料': 65, '医疗器械': 70, '消费电子': 65,
            '家电': 60, '汽车': 60, '化工': 55, '机械': 55,
            
            # 传统行业 (低分)
            '银行': 45, '保险': 40, '地产': 35, '钢铁': 40,
            '煤炭': 45, '石油': 40, '建筑': 35, '有色': 45
        }
    
    def get_industry_info(self, stock_code):
        """获取行业信息"""
        if not ak:
            return "未知行业", 50
        
        try:
            stock_info = ak.stock_individual_info_em(symbol=stock_code)
            industry = "未知行业"
            
            if not stock_info.empty:
                for _, row in stock_info.iterrows():
                    if '行业' in row['item']:
                        industry = row['value']
                        break
            
            # 匹配行业评分
            score = 50  # 默认分数
            for key, value in self.industry_scores.items():
                if key in industry:
                    score = value
                    break
            
            return industry, score
            
        except Exception as e:
            print(f"获取 {stock_code} 行业信息失败: {e}")
            return "未知行业", 50

class EnhancedStockScorer:
    """增强版股票评分系统"""
    
    def __init__(self):
        # 四维评分权重
        self.weights = {
            # 技术面 (60%)
            'macd': 0.10,
            'rsi': 0.08,
            'kdj': 0.08,
            'bollinger': 0.06,
            'volume_obv': 0.12,  # 提升成交量权重
            'ma_trend': 0.06,
            'adx_strength': 0.10,  # 新增趋势强度
            
            # 基本面 (25%)
            'fundamentals': 0.25,
            
            # 市场情绪 (10%)
            'price_momentum': 0.03,
            'volume_momentum': 0.04,
            'volatility': 0.03,
            
            # 行业因子 (5%)
            'industry': 0.05
        }
        
        self.fundamental_analyzer = FundamentalAnalyzer()
        self.industry_analyzer = IndustryAnalyzer()
    
    def calculate_enhanced_score(self, stock_data, stock_code):
        """计算增强版综合评分"""
        if stock_data.empty or len(stock_data) < 30:
            return 0, [], {}
        
        try:
            scores_detail = {}
            all_reasons = []
            
            # 提取数据
            high = stock_data['high']
            low = stock_data['low']
            close = stock_data['close']
            volume = stock_data['volume']
            
            # 1. 技术指标评分 (60%)
            tech_score, tech_reasons = self._calculate_technical_score(high, low, close, volume)
            scores_detail['技术面'] = tech_score
            all_reasons.extend(tech_reasons)
            
            # 2. 基本面评分 (25%)
            fundamental_score, fund_reasons = self._calculate_fundamental_score(stock_code)
            scores_detail['基本面'] = fundamental_score
            all_reasons.extend(fund_reasons)
            
            # 3. 市场情绪评分 (10%)
            sentiment_score, sent_reasons = self._calculate_sentiment_score(close, volume)
            scores_detail['市场情绪'] = sentiment_score
            all_reasons.extend(sent_reasons)
            
            # 4. 行业因子评分 (5%)
            industry_name, industry_score = self.industry_analyzer.get_industry_info(stock_code)
            scores_detail['行业'] = industry_score
            all_reasons.append(f"{industry_name}")
            
            # 计算加权总分
            total_score = (
                tech_score * 0.60 +
                fundamental_score * 0.25 +
                sentiment_score * 0.10 +
                industry_score * 0.05
            )
            
            return min(100, max(0, total_score)), all_reasons, scores_detail
            
        except Exception as e:
            print(f"计算增强评分时出错: {e}")
            return 0, [], {}
    
    def _calculate_technical_score(self, high, low, close, volume):
        """计算技术面评分"""
        score = 0
        reasons = []
        
        try:
            # MACD评分
            dif, dea, macd = TechnicalIndicators.calculate_macd(close)
            if not dif.empty and not dea.empty and len(dif) > 1:
                if dif.iloc[-1] > dea.iloc[-1] and dif.iloc[-2] <= dea.iloc[-2]:
                    score += 25
                    reasons.append("MACD金叉")
                elif dif.iloc[-1] > 0:
                    score += 15
                    reasons.append("MACD多头")
            
            # RSI评分
            rsi = TechnicalIndicators.calculate_rsi(close)
            if not rsi.empty:
                rsi_val = rsi.iloc[-1]
                if 30 <= rsi_val <= 70:
                    score += 20
                    reasons.append("RSI正常")
                elif rsi_val < 30:
                    score += 25
                    reasons.append("RSI超卖反弹")
            
            # KDJ评分
            k, d, j = TechnicalIndicators.calculate_kdj(high, low, close)
            if not k.empty and not d.empty and len(k) > 1:
                if k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2] and j.iloc[-1] < 80:
                    score += 20
                    reasons.append("KDJ金叉")
            
            # 布林带评分
            upper, middle, lower = TechnicalIndicators.calculate_bollinger_bands(close)
            if not lower.empty and not middle.empty:
                current_price = close.iloc[-1]
                if abs(current_price - lower.iloc[-1]) / lower.iloc[-1] <= 0.02:
                    score += 15
                    reasons.append("布林带下轨反弹")
                elif len(close) > 1 and close.iloc[-1] > middle.iloc[-1] and close.iloc[-2] <= middle.iloc[-2]:
                    score += 12
                    reasons.append("突破布林带中轨")
            
            # ADX趋势强度评分
            adx, plus_di, minus_di = EnhancedTechnicalIndicators.calculate_adx(high, low, close)
            if not adx.empty:
                adx_val = adx.iloc[-1]
                if adx_val > 25:
                    score += 20
                    reasons.append("趋势强劲")
                elif adx_val > 20:
                    score += 15
                    reasons.append("趋势明确")
            
            # 威廉指标评分
            wr = EnhancedTechnicalIndicators.calculate_williams_r(high, low, close)
            if not wr.empty:
                wr_val = wr.iloc[-1]
                if -80 <= wr_val <= -20:
                    score += 10
                    reasons.append("威廉指标正常")
            
            # OBV成交量评分
            obv = EnhancedTechnicalIndicators.calculate_obv(close, volume)
            if not obv.empty and len(obv) > 10:
                obv_ma = obv.rolling(window=10).mean()
                if not obv_ma.empty and obv.iloc[-1] > obv_ma.iloc[-1]:
                    score += 20
                    reasons.append("资金流入")
            
            # 均线多头排列
            if TechnicalIndicators.check_ma_bullish_arrangement(close):
                score += 15
                reasons.append("均线多头排列")
            
            # 成交量放大
            if TechnicalIndicators.check_volume_amplification(volume):
                score += 15
                reasons.append("成交量放大")
                
        except Exception as e:
            print(f"技术面评分计算出错: {e}")
        
        return min(100, score), reasons
    
    def _calculate_fundamental_score(self, stock_code):
        """计算基本面评分"""
        financial_data = self.fundamental_analyzer.get_financial_data(stock_code)
        return self.fundamental_analyzer.score_fundamentals(financial_data)
    
    def _calculate_sentiment_score(self, close, volume):
        """计算市场情绪评分"""
        score = 0
        reasons = []
        
        try:
            # 价格动量评分
            momentum = MarketSentimentAnalyzer.calculate_price_momentum(close)
            if not momentum.empty:
                momentum_val = momentum.iloc[-1]
                if momentum_val > 5:
                    score += 20
                    reasons.append("价格动量积极")
                elif momentum_val > 0:
                    score += 10
                    reasons.append("价格动量正面")
            
            # 成交量动量评分
            vol_momentum = MarketSentimentAnalyzer.calculate_volume_momentum(volume)
            if not vol_momentum.empty:
                vol_momentum_val = vol_momentum.iloc[-1]
                if vol_momentum_val > 1.5:
                    score += 25
                    reasons.append("成交活跃")
                elif vol_momentum_val > 1.2:
                    score += 15
                    reasons.append("成交量增加")
            
            # 波动率评分
            volatility_score = MarketSentimentAnalyzer.calculate_volatility_score(close)
            if not volatility_score.empty:
                vol_score_val = volatility_score.iloc[-1]
                if vol_score_val > 70:
                    score += 15
                    reasons.append("波动率适中")
                    
        except Exception as e:
            print(f"市场情绪评分计算出错: {e}")
        
        return min(100, score), reasons

class EnhancedPersonalStockSelector:
    """增强版个人选股系统"""
    
    def __init__(self, config=None):
        self.config = config or self._default_enhanced_config()
        self.scorer = EnhancedStockScorer()
        
        # 创建结果存储目录
        if not os.path.exists('enhanced_results'):
            os.makedirs('enhanced_results')
    
    def _default_enhanced_config(self):
        """增强版默认配置"""
        return {
            'min_market_cap': 8000000000,    # 提升到80亿
            'max_recent_gain': 25,           # 降低到25%
            'min_score': 75,                 # 提升到75分
            'max_stocks': 8,                 # 减少到8只精选
            'analysis_period': 60,           # 分析周期
            'sample_size': 50,               # 样本大小
            
            # 基本面要求
            'max_pe': 35,                    # PE上限
            'min_roe': 3,                    # ROE下限
            'max_pb': 6,                     # PB上限
            
            # 技术面要求
            'min_adx': 15,                   # 最小趋势强度
            'volume_amplify': 1.5,           # 成交量放大倍数
        }
    
    def enhanced_stock_selection(self):
        """增强版选股主函数"""
        print(f"🚀 开始执行增强版选股 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # 1. 获取和筛选股票
            candidate_stocks = self._get_candidate_stocks()
            
            if not candidate_stocks:
                print("没有符合基础筛选条件的股票")
                return []
            
            # 2. 增强版评分分析
            scored_stocks = self._enhanced_scoring(candidate_stocks)
            
            if not scored_stocks:
                print("没有符合评分要求的股票")
                return []
            
            # 3. 排序并取前N名
            top_stocks = sorted(
                scored_stocks,
                key=lambda x: x['total_score'],
                reverse=True
            )[:self.config['max_stocks']]
            
            # 4. 保存和展示结果
            self._save_enhanced_results(top_stocks)
            self._print_enhanced_results(top_stocks)
            
            return top_stocks
            
        except Exception as e:
            print(f"增强版选股过程出错: {e}")
            return []
    
    def _get_candidate_stocks(self):
        """获取候选股票池"""
        print("正在筛选候选股票...")
        
        # 预定义优质股票池（实际应用中从数据源获取）
        candidate_pool = [
            {'code': '000001', 'name': '平安银行'},
            {'code': '000002', 'name': '万科A'},
            {'code': '000858', 'name': '五粮液'},
            {'code': '000876', 'name': '新希望'},
            {'code': '002415', 'name': '海康威视'},
            {'code': '002594', 'name': '比亚迪'},
            {'code': '600036', 'name': '招商银行'},
            {'code': '600519', 'name': '贵州茅台'},
            {'code': '600887', 'name': '伊利股份'},
            {'code': '000858', 'name': '五粮液'},
        ]
        
        print(f"候选股票池: {len(candidate_pool)} 只")
        return candidate_pool
    
    def _enhanced_scoring(self, candidate_stocks):
        """增强版评分分析"""
        print("正在进行增强版评分分析...")
        scored_stocks = []
        
        for idx, stock in enumerate(candidate_stocks):
            print(f"分析 {stock['name']} ({stock['code']}) [{idx+1}/{len(candidate_stocks)}]")
            
            try:
                # 生成模拟数据（实际应用中从akshare获取）
                stock_data = self._generate_sample_data()
                
                if stock_data.empty:
                    continue
                
                # 计算增强版评分
                total_score, reasons, scores_detail = self.scorer.calculate_enhanced_score(
                    stock_data, stock['code']
                )
                
                if total_score >= self.config['min_score']:
                    scored_stocks.append({
                        'code': stock['code'],
                        'name': stock['name'],
                        'total_score': round(total_score, 1),
                        'scores_detail': scores_detail,
                        'reasons': reasons,
                        'current_price': round(stock_data['close'].iloc[-1], 2)
                    })
                    
                    print(f"  ✅ 评分: {total_score:.1f}")
                else:
                    print(f"  ❌ 评分: {total_score:.1f} (低于阈值)")
                    
                time.sleep(0.1)  # 避免请求过频
                
            except Exception as e:
                print(f"  ❌ 分析失败: {e}")
                continue
        
        return scored_stocks
    
    def _generate_sample_data(self):
        """生成示例数据（用于演示）"""
        # 生成60天的示例股票数据
        dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
        
        np.random.seed(42)
        base_price = 10
        prices = []
        volumes = []
        
        for i in range(60):
            # 模拟价格走势
            change = np.random.normal(0, 0.02)
            base_price *= (1 + change)
            prices.append(base_price)
            
            # 模拟成交量
            volume = np.random.randint(1000000, 5000000)
            volumes.append(volume)
        
        # 生成高低价
        highs = [p * (1 + np.random.uniform(0, 0.03)) for p in prices]
        lows = [p * (1 - np.random.uniform(0, 0.03)) for p in prices]
        
        return pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': highs,
            'low': lows,
            'close': prices,
            'volume': volumes
        })
    
    def _save_enhanced_results(self, stocks):
        """保存增强版选股结果"""
        today = datetime.now().strftime('%Y-%m-%d')
        filename = f"enhanced_results/enhanced_selection_{today}.json"
        
        result_data = {
            'date': today,
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'stocks': stocks,
            'summary': {
                'total_recommended': len(stocks),
                'avg_score': round(sum(s['total_score'] for s in stocks) / len(stocks), 1) if stocks else 0,
                'score_range': [
                    min(s['total_score'] for s in stocks),
                    max(s['total_score'] for s in stocks)
                ] if stocks else [0, 0]
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 结果已保存到: {filename}")
        except Exception as e:
            print(f"❌ 保存结果失败: {e}")
    
    def _print_enhanced_results(self, stocks):
        """打印增强版选股结果"""
        if not stocks:
            print("📭 今日无推荐股票")
            return
        
        print(f"\n🏆 增强版选股推荐 - {datetime.now().strftime('%Y-%m-%d')}")
        print("=" * 70)
        
        for i, stock in enumerate(stocks, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            print(f"\n{medal} {stock['name']} ({stock['code']}) - 综合评分: {stock['total_score']}/100")
            print(f"   💰 当前价格: ¥{stock['current_price']}")
            
            # 显示各维度评分
            if 'scores_detail' in stock:
                detail = stock['scores_detail']
                print(f"   📊 评分详情:")
                for dimension, score in detail.items():
                    print(f"      {dimension}: {score:.1f}分")
            
            # 显示推荐理由
            if stock['reasons']:
                print(f"   🎯 推荐理由: {' | '.join(stock['reasons'][:5])}")  # 只显示前5个理由
        
        avg_score = sum(s['total_score'] for s in stocks) / len(stocks)
        print(f"\n📈 统计信息:")
        print(f"   推荐股票数: {len(stocks)} 只")
        print(f"   平均评分: {avg_score:.1f}/100")
        print(f"   评分范围: {min(s['total_score'] for s in stocks):.1f} - {max(s['total_score'] for s in stocks):.1f}")
        
        print(f"\n⚠️  风险提示:")
        print(f"   本推荐基于增强版四维分析模型，仅供参考，不构成投资建议")
        print(f"   股市有风险，投资需谨慎，请结合个人风险承受能力")

# 使用示例和测试
def main():
    """主函数 - 演示增强版选股系统"""
    print("🚀 增强版A股选股系统")
    print("集成技术面、基本面、资金面、行业面四维分析")
    print("=" * 50)
    
    # 创建增强版选股器
    enhanced_selector = EnhancedPersonalStockSelector()
    
    # 执行增强版选股
    results = enhanced_selector.enhanced_stock_selection()
    
    if results:
        print(f"\n🎉 选股完成！共推荐 {len(results)} 只优质股票")
    else:
        print(f"\n😔 暂无符合条件的推荐股票，建议降低评分要求或扩大候选池")

if __name__ == "__main__":
    main() 