#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 简化版智能选股系统 v1.0
无需ta-lib依赖，立即可用！

特点：
- 基础技术指标计算（MA、RSI、MACD）
- 微信自动推送
- 数据实时获取
- 多维度评分
"""

import pandas as pd
import numpy as np
import akshare as ak
import json
import requests
import time
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

class SimpleStockSelector:
    def __init__(self):
        self.notification_config = self.load_config()
        print("🚀 简化版选股系统启动...")
        
    def load_config(self):
        """加载通知配置"""
        try:
            with open('notification_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'wechat_enabled': False}
    
    def calculate_ma(self, data, window):
        """计算移动平均线"""
        return data.rolling(window=window).mean()
    
    def calculate_rsi(self, data, window=14):
        """计算RSI指标"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, data, fast=12, slow=26, signal=9):
        """计算MACD指标"""
        exp1 = data.ewm(span=fast).mean()
        exp2 = data.ewm(span=slow).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def get_stock_list(self):
        """获取股票列表"""
        try:
            print("📊 获取股票列表...")
            # 获取沪深A股实时行情
            stock_list = ak.stock_zh_a_spot_em()
            
            # 基础筛选
            filtered = stock_list[
                (stock_list['流通市值'] > 50e8) &  # 流通市值>50亿
                (~stock_list['名称'].str.contains('ST|退')) &  # 排除ST股
                (stock_list['涨跌幅'] < 30) &  # 排除异常涨幅
                (stock_list['涨跌幅'] > -30)   # 排除异常跌幅
            ].copy()
            
            print(f"✅ 获取到 {len(filtered)} 只符合条件的股票")
            return filtered
            
        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def analyze_stock(self, code, name):
        """分析单只股票"""
        try:
            # 获取日K数据
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=code, period="daily", 
                                  start_date=start_date, end_date=end_date)
            
            if df.empty or len(df) < 30:
                return None
                
            df = df.sort_values('日期').reset_index(drop=True)
            
            # 计算技术指标
            df['MA5'] = self.calculate_ma(df['收盘'], 5)
            df['MA10'] = self.calculate_ma(df['收盘'], 10)
            df['MA20'] = self.calculate_ma(df['收盘'], 20)
            df['RSI'] = self.calculate_rsi(df['收盘'])
            
            macd, signal, histogram = self.calculate_macd(df['收盘'])
            df['MACD'] = macd
            df['SIGNAL'] = signal
            df['HISTOGRAM'] = histogram
            
            # 获取最新数据
            latest = df.iloc[-1]
            prev = df.iloc[-2] if len(df) > 1 else latest
            
            # 计算评分
            score = self.calculate_score(df, latest, prev)
            
            return {
                'code': code,
                'name': name,
                'price': latest['收盘'],
                'change_pct': (latest['收盘'] - prev['收盘']) / prev['收盘'] * 100,
                'volume': latest['成交量'],
                'score': score,
                'ma5': latest['MA5'],
                'ma10': latest['MA10'],
                'ma20': latest['MA20'],
                'rsi': latest['RSI'],
                'macd': latest['MACD'],
                'signal': latest['SIGNAL']
            }
            
        except Exception as e:
            # print(f"分析股票 {code} 失败: {e}")
            return None
    
    def calculate_score(self, df, latest, prev):
        """计算股票评分"""
        score = 0
        
        # 价格趋势 (30分)
        if latest['收盘'] > latest['MA5'] > latest['MA10'] > latest['MA20']:
            score += 30  # 多头排列
        elif latest['收盘'] > latest['MA5']:
            score += 15  # 短期向上
        
        # RSI指标 (20分)
        rsi = latest['RSI']
        if 30 <= rsi <= 70:  # 正常区间
            score += 20
        elif 20 <= rsi < 30:  # 超卖区间
            score += 15
        
        # MACD指标 (25分)
        if latest['MACD'] > latest['SIGNAL'] and latest['MACD'] > 0:
            score += 25  # 金叉且在0轴上方
        elif latest['MACD'] > latest['SIGNAL']:
            score += 15  # 金叉
        
        # 成交量 (15分)
        vol_ma = df['成交量'].tail(5).mean()
        if latest['成交量'] > vol_ma * 1.5:
            score += 15  # 放量
        elif latest['成交量'] > vol_ma:
            score += 10
        
        # 涨跌幅 (10分)
        change_pct = (latest['收盘'] - prev['收盘']) / prev['收盘'] * 100
        if 0 < change_pct <= 5:
            score += 10  # 适度上涨
        elif -2 <= change_pct <= 0:
            score += 5   # 小幅调整
        
        return min(score, 100)  # 最高100分
    
    def scan_stocks(self, sample_size=200):
        """扫描股票"""
        print(f"\n🔍 开始扫描股票 (样本数: {sample_size})")
        
        # 获取股票列表
        stock_list = self.get_stock_list()
        if stock_list.empty:
            return []
        
        # 随机采样
        if len(stock_list) > sample_size:
            stock_list = stock_list.sample(n=sample_size, random_state=42)
        
        results = []
        processed = 0
        start_time = time.time()
        
        for _, stock in stock_list.iterrows():
            code = stock['代码']
            name = stock['名称']
            
            analysis = self.analyze_stock(code, name)
            if analysis and analysis['score'] >= 60:  # 评分>=60才推荐
                results.append(analysis)
            
            processed += 1
            if processed % 20 == 0:
                elapsed = time.time() - start_time
                print(f"📈 已处理 {processed}/{len(stock_list)} 只股票，耗时 {elapsed:.1f}秒")
        
        # 按评分排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        elapsed = time.time() - start_time
        print(f"\n✅ 扫描完成！")
        print(f"⏱️  总耗时: {elapsed:.1f}秒")
        print(f"📊 找到 {len(results)} 只优质股票")
        
        return results[:15]  # 返回前15只
    
    def send_wechat_notification(self, stocks):
        """发送微信通知"""
        if not self.notification_config.get('wechat_enabled'):
            print("📱 微信通知未启用")
            return False
            
        wechat_key = self.notification_config.get('wechat_key')
        if not wechat_key:
            print("❌ 微信Key未配置")
            return False
        
        try:
            # 生成报告内容
            title = f"🚀 智能选股 - 今日推荐 ({len(stocks)}只)"
            
            content = f"# 📊 每日选股报告\n\n"
            content += f"🕐 扫描时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            content += f"📈 推荐数量: {len(stocks)}只\n\n"
            
            if stocks:
                content += "## 🏆 TOP推荐:\n\n"
                
                for i, stock in enumerate(stocks[:5], 1):
                    emoji = ["🥇", "🥈", "🥉", "🏅", "⭐"][i-1]
                    content += f"**{emoji} {stock['name']} ({stock['code']})**\n"
                    content += f"- 💰 价格: ¥{stock['price']:.2f} ({stock['change_pct']:+.2f}%)\n"
                    content += f"- 📊 评分: {stock['score']:.0f}/100\n"
                    content += f"- 📈 RSI: {stock['rsi']:.1f}\n\n"
                
                if len(stocks) > 5:
                    content += f"## 📋 其他推荐 ({len(stocks)-5}只):\n\n"
                    for stock in stocks[5:]:
                        content += f"• {stock['name']} ({stock['code']}) - {stock['score']:.0f}分\n"
            else:
                content += "## 📉 今日无推荐\n\n"
                content += "暂未发现符合条件的优质股票，建议继续观望。\n"
            
            content += f"\n## ⚠️ 风险提醒\n"
            content += f"- 本分析仅供参考，不构成投资建议\n"
            content += f"- 股市有风险，投资需谨慎\n\n"
            content += f"---\n🤖 简化版选股系统 v1.0"
            
            # 发送通知
            url = f"https://sctapi.ftqq.com/{wechat_key}.send"
            data = {'title': title, 'desp': content}
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    print("✅ 微信通知发送成功！")
                    return True
                else:
                    print(f"❌ 微信通知发送失败: {result.get('message')}")
            else:
                print(f"❌ 请求失败，状态码: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 发送微信通知异常: {e}")
        
        return False
    
    def run(self):
        """运行选股系统"""
        print("="*60)
        print("🚀 简化版智能选股系统 v1.0")
        print("📅", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        print("="*60)
        
        # 扫描股票
        stocks = self.scan_stocks(sample_size=200)
        
        # 显示结果
        if stocks:
            print(f"\n📋 今日推荐股票 (TOP {len(stocks)}):")
            print("-" * 80)
            print(f"{'排名':<4} {'代码':<8} {'名称':<10} {'价格':<8} {'涨幅%':<8} {'评分':<6} {'RSI':<6}")
            print("-" * 80)
            
            for i, stock in enumerate(stocks, 1):
                print(f"{i:<4} {stock['code']:<8} {stock['name']:<10} "
                      f"{stock['price']:<8.2f} {stock['change_pct']:<8.2f} "
                      f"{stock['score']:<6.0f} {stock['rsi']:<6.1f}")
            
            # 发送微信通知
            self.send_wechat_notification(stocks)
        else:
            print("\n📉 今日无推荐股票")
            self.send_wechat_notification([])
        
        print("\n🎯 选股任务完成！")

def main():
    """主函数"""
    try:
        selector = SimpleStockSelector()
        selector.run()
    except KeyboardInterrupt:
        print("\n\n⏹️  用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")

if __name__ == "__main__":
    main() 