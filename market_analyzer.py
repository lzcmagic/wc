#!/usr/bin/env python3
"""
Market Data Analyzer - Professional Financial Analysis Tool
Real-time A-share market analysis and portfolio optimization
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
import warnings
warnings.filterwarnings('ignore')

try:
    import akshare as ak
    AK_AVAILABLE = True
except ImportError:
    AK_AVAILABLE = False
    print("Warning: akshare not available. Install with: pip install akshare")

class TechnicalIndicators:
    """Technical Analysis Indicators Module"""
    
    @staticmethod
    def calculate_ma(data, periods=[5, 10, 20]):
        """Moving Average calculation"""
        mas = {}
        for period in periods:
            mas[f'ma{period}'] = data.rolling(window=period).mean()
        return mas
    
    @staticmethod
    def calculate_macd(close_price, fast=12, slow=26, signal=9):
        """MACD Indicator"""
        exp1 = close_price.ewm(span=fast).mean()
        exp2 = close_price.ewm(span=slow).mean()
        dif = exp1 - exp2
        dea = dif.ewm(span=signal).mean()
        macd = (dif - dea) * 2
        return dif, dea, macd
    
    @staticmethod
    def calculate_rsi(close_price, period=14):
        """RSI Indicator"""
        delta = close_price.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)
    
    @staticmethod
    def calculate_kdj(high, low, close, period=9):
        """KDJ Indicator"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
        rsv = rsv.fillna(50)
        
        k = rsv.ewm(alpha=1/3).mean()
        d = k.ewm(alpha=1/3).mean()
        j = 3 * k - 2 * d
        
        return k.fillna(50), d.fillna(50), j.fillna(50)

class MarketDataProvider:
    """Real-time Market Data Provider"""
    
    def __init__(self):
        self.cache = {}
        self.last_update = None
        
    def get_stock_list(self):
        """Get complete A-share stock list (5000+ stocks)"""
        if not AK_AVAILABLE:
            return self._get_fallback_stock_list()
        
        try:
            # Get complete A-share list
            raw_data = ak.stock_zh_a_spot_em()
            
            # Filter and clean - ensure we have a DataFrame
            stock_list: pd.DataFrame = raw_data[['代码', '名称', '最新价', '总市值', '流通市值']].copy()
            stock_list.columns = ['code', 'name', 'price', 'market_cap', 'float_cap']
            
            # Remove ST stocks and special cases
            try:
                mask = ~stock_list['name'].astype(str).str.contains('ST|退市|暂停', na=False)
                stock_list = stock_list[mask]
            except:
                pass  # Skip filtering if there's an issue
            
            # Convert market cap to numeric
            stock_list['market_cap'] = pd.to_numeric(stock_list['market_cap'], errors='coerce')
            stock_list['float_cap'] = pd.to_numeric(stock_list['float_cap'], errors='coerce')
            
            # Filter by market cap (>5 billion)
            stock_list = stock_list[stock_list['market_cap'] > 5000000000]
            
            print(f"✓ Loaded {len(stock_list)} stocks from A-share market")
            return stock_list.reset_index(drop=True)
            
        except Exception as e:
            print(f"Error loading stock list: {e}")
            return self._get_fallback_stock_list()
    
    def _get_fallback_stock_list(self):
        """Fallback stock list for testing"""
        return pd.DataFrame({
            'code': ['000001', '000002', '000858', '002415', '002594', '600036', '600519', '600887'],
            'name': ['平安银行', '万科A', '五粮液', '海康威视', '比亚迪', '招商银行', '贵州茅台', '伊利股份'],
            'price': [12.5, 18.3, 180.5, 32.8, 245.3, 35.7, 1680.8, 28.9],
            'market_cap': [24000000000, 20000000000, 72000000000, 28000000000, 70000000000, 
                          42000000000, 210000000000, 18000000000],
            'float_cap': [24000000000, 20000000000, 72000000000, 28000000000, 70000000000, 
                         42000000000, 210000000000, 18000000000]
        })
    
    def get_stock_data(self, stock_code, period=60):
        """Get historical stock data"""
        if not AK_AVAILABLE:
            return self._generate_sample_data()
        
        try:
            # Get historical data
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=period*2)).strftime('%Y%m%d')
            
            stock_data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", 
                                          start_date=start_date, end_date=end_date)
            
            if stock_data.empty:
                return None
            
            # Standardize column names
            stock_data.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude',
                                'pct_change', 'change', 'turnover']
            
            # Convert to numeric
            numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount']
            for col in numeric_cols:
                stock_data[col] = pd.to_numeric(stock_data[col], errors='coerce')
            
            return stock_data.tail(period).reset_index(drop=True)
            
        except Exception as e:
            print(f"Error getting data for {stock_code}: {e}")
            return None
    
    def _generate_sample_data(self, days=60):
        """Generate sample data for testing"""
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Simulate realistic price movement
        np.random.seed(42)
        base_price = np.random.uniform(10, 100)
        prices = [base_price]
        
        for i in range(1, days):
            change = np.random.normal(0, 0.02)
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 0.1))  # Prevent negative prices
        
        # Generate OHLC data
        data = []
        for i, price in enumerate(prices):
            high = price * (1 + abs(np.random.normal(0, 0.01)))
            low = price * (1 - abs(np.random.normal(0, 0.01)))
            open_price = prices[i-1] if i > 0 else price
            volume = np.random.randint(1000000, 10000000)
            
            data.append({
                'date': dates[i],
                'open': round(open_price, 2),
                'high': round(high, 2),
                'low': round(low, 2),
                'close': round(price, 2),
                'volume': volume,
                'amount': volume * price
            })
        
        return pd.DataFrame(data)

class PortfolioOptimizer:
    """Advanced Portfolio Optimization Engine"""
    
    def __init__(self):
        self.data_provider = MarketDataProvider()
        self.indicators = TechnicalIndicators()
        
    def calculate_composite_score(self, stock_data):
        """Calculate composite technical score"""
        if stock_data is None or len(stock_data) < 30:
            return 0, []
        
        score = 0
        signals = []
        
        try:
            high = stock_data['high']
            low = stock_data['low']
            close = stock_data['close']
            volume = stock_data['volume']
            
            # MACD Analysis (25%)
            dif, dea, macd = self.indicators.calculate_macd(close)
            if len(dif) > 1 and dif.iloc[-1] > dea.iloc[-1]:
                if dif.iloc[-2] <= dea.iloc[-2]:
                    score += 25
                    signals.append("MACD Golden Cross")
                else:
                    score += 15
                    signals.append("MACD Bullish")
            
            # RSI Analysis (20%)
            rsi = self.indicators.calculate_rsi(close)
            rsi_val = rsi.iloc[-1]
            if 30 <= rsi_val <= 70:
                score += 20
                signals.append("RSI Normal")
            elif rsi_val < 30:
                score += 25
                signals.append("RSI Oversold")
            
            # KDJ Analysis (20%)
            k, d, j = self.indicators.calculate_kdj(high, low, close)
            if len(k) > 1 and k.iloc[-1] > d.iloc[-1] and k.iloc[-2] <= d.iloc[-2]:
                if j.iloc[-1] < 80:
                    score += 20
                    signals.append("KDJ Golden Cross")
            
            # Moving Average Analysis (15%)
            mas = self.indicators.calculate_ma(close, [5, 10, 20])
            current_price = close.iloc[-1]
            if (current_price > mas['ma5'].iloc[-1] > mas['ma10'].iloc[-1] > mas['ma20'].iloc[-1]):
                score += 15
                signals.append("MA Bullish Alignment")
            
            # Volume Analysis (20%)
            avg_volume = volume.rolling(20).mean().iloc[-1]
            current_volume = volume.iloc[-1]
            if current_volume > avg_volume * 1.5:
                score += 20
                signals.append("Volume Surge")
            elif current_volume > avg_volume * 1.2:
                score += 10
                signals.append("Volume Increase")
            
        except Exception as e:
            print(f"Error calculating score: {e}")
            return 0, []
        
        return min(100, score), signals
    
    def scan_market(self, min_score=70, max_results=10):
        """Scan entire market for opportunities"""
        print("=" * 60)
        print("🔍 Market Analysis Engine - Real-time Scanning")
        print("=" * 60)
        
        # Get stock universe
        stock_list = self.data_provider.get_stock_list()
        total_stocks = len(stock_list)
        
        print(f"📊 Analyzing {total_stocks} stocks from A-share market...")
        print(f"🎯 Target: Top {max_results} stocks with score >= {min_score}")
        print("")
        
        results = []
        processed = 0
        
        # Sample stocks for analysis (to avoid overwhelming API)
        sample_size = min(200, total_stocks)  # Analyze up to 200 stocks
        stock_sample = stock_list.sample(n=sample_size).reset_index(drop=True)
        
        for idx, row in stock_sample.iterrows():
            stock_code = row['code']
            stock_name = row['name']
            
            processed += 1
            
            # Progress indicator
            if processed % 20 == 0:
                print(f"⏳ Progress: {processed}/{sample_size} stocks analyzed...")
            
            # Get stock data and calculate score
            stock_data = self.data_provider.get_stock_data(stock_code)
            score, signals = self.calculate_composite_score(stock_data)
            
            if score >= min_score:
                results.append({
                    'code': stock_code,
                    'name': stock_name,
                    'score': score,
                    'price': row['price'],
                    'market_cap': row['market_cap'],
                    'signals': signals
                })
                
                print(f"✓ {stock_name} ({stock_code}) - Score: {score}")
            
            # Rate limiting
            time.sleep(0.1)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]
    
    def generate_report(self, results):
        """Generate professional analysis report"""
        if not results:
            print("\n📭 No qualifying opportunities found in current market scan")
            print("💡 Consider adjusting parameters or scanning again later")
            return
        
        print(f"\n🏆 TOP MARKET OPPORTUNITIES - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("=" * 70)
        
        for i, stock in enumerate(results, 1):
            rank_icon = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            print(f"\n{rank_icon} {stock['name']} ({stock['code']})")
            print(f"    📊 Composite Score: {stock['score']}/100")
            print(f"    💰 Current Price: ¥{stock['price']}")
            print(f"    🏢 Market Cap: ¥{stock['market_cap']:,.0f}")
            
            if stock['signals']:
                print(f"    🎯 Key Signals: {' | '.join(stock['signals'][:3])}")
        
        # Summary statistics
        avg_score = sum(s['score'] for s in results) / len(results)
        print(f"\n📈 SCAN SUMMARY:")
        print(f"    Total Opportunities: {len(results)}")
        print(f"    Average Score: {avg_score:.1f}/100")
        print(f"    Score Range: {min(s['score'] for s in results)}-{max(s['score'] for s in results)}")
        
        print(f"\n⚠️  RISK DISCLAIMER:")
        print(f"    This analysis is for research purposes only")
        print(f"    Past performance does not guarantee future results")

def main():
    """Main execution function"""
    print("Market Data Analyzer v2.0")
    print("Professional Financial Analysis Tool")
    print("-" * 40)
    
    # Initialize optimizer
    optimizer = PortfolioOptimizer()
    
    # Scan market for opportunities
    results = optimizer.scan_market(min_score=70, max_results=10)
    
    # Generate report
    optimizer.generate_report(results)
    
    print(f"\n💡 Quick Commands:")
    print(f"    python market_analyzer.py              # Full market scan")
    print(f"    python -c 'from market_analyzer import *; PortfolioOptimizer().scan_market(60, 15)'  # Custom scan")

if __name__ == "__main__":
    main() 