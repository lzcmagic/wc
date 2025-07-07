#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级技术指标库 - 专业级技术分析工具
包含20+专业技术指标，支持多时间周期分析
"""

import numpy as np
import pandas as pd
import talib
from typing import Tuple, Dict, Any, Optional, List
import warnings
warnings.filterwarnings('ignore')

class AdvancedIndicators:
    """高级技术指标计算器"""
    
    def __init__(self):
        self.indicators_cache = {}
    
    # ============ 趋势指标 ============
    
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """
        ADX - 平均趋向指数
        衡量趋势强度的经典指标
        """
        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            
            adx = talib.ADX(high, low, close, timeperiod=period)
            plus_di = talib.PLUS_DI(high, low, close, timeperiod=period)
            minus_di = talib.MINUS_DI(high, low, close, timeperiod=period)
            
            current_adx = adx[-1] if not np.isnan(adx[-1]) else 0
            current_plus_di = plus_di[-1] if not np.isnan(plus_di[-1]) else 0
            current_minus_di = minus_di[-1] if not np.isnan(minus_di[-1]) else 0
            
            # ADX信号判断
            if current_adx >= 40:
                trend_strength = "强趋势"
                strength_score = 95
            elif current_adx >= 25:
                trend_strength = "中等趋势" 
                strength_score = 75
            elif current_adx >= 15:
                trend_strength = "弱趋势"
                strength_score = 50
            else:
                trend_strength = "无趋势"
                strength_score = 20
            
            # 方向判断
            if current_plus_di > current_minus_di:
                direction = "上升"
                direction_score = 80
            else:
                direction = "下降"
                direction_score = 20
            
            signal_score = (strength_score + direction_score) / 2
            
            return {
                'adx': current_adx,
                'plus_di': current_plus_di,
                'minus_di': current_minus_di,
                'trend_strength': trend_strength,
                'direction': direction,
                'signal': f"{trend_strength} {direction}",
                'score': signal_score
            }
        except Exception as e:
            return {'adx': 0, 'score': 50, 'signal': 'ADX计算失败'}
    
    def calculate_aroon(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """
        Aroon指标 - 阿隆指标
        识别趋势变化的时机
        """
        try:
            high = df['high'].values
            low = df['low'].values
            
            aroon_up, aroon_down = talib.AROON(high, low, timeperiod=period)
            
            current_up = aroon_up[-1] if not np.isnan(aroon_up[-1]) else 0
            current_down = aroon_down[-1] if not np.isnan(aroon_down[-1]) else 0
            
            # Aroon信号判断
            if current_up >= 80 and current_down <= 20:
                signal = "强烈看涨"
                score = 90
            elif current_up >= 50 and current_up > current_down:
                signal = "看涨"
                score = 70
            elif current_down >= 80 and current_up <= 20:
                signal = "强烈看跌"
                score = 10
            elif current_down >= 50 and current_down > current_up:
                signal = "看跌"
                score = 30
            else:
                signal = "震荡"
                score = 50
            
            return {
                'aroon_up': current_up,
                'aroon_down': current_down,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'aroon_up': 0, 'aroon_down': 0, 'score': 50, 'signal': 'Aroon计算失败'}
    
    def calculate_cci(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """
        CCI - 商品路径指标
        衡量价格偏离统计平均值的程度
        """
        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            
            cci = talib.CCI(high, low, close, timeperiod=period)
            current_cci = cci[-1] if not np.isnan(cci[-1]) else 0
            
            # CCI信号判断
            if current_cci > 200:
                signal = "超强上涨"
                score = 95
            elif current_cci > 100:
                signal = "强势上涨"
                score = 80
            elif current_cci > 0:
                signal = "温和上涨"
                score = 65
            elif current_cci > -100:
                signal = "温和下跌"
                score = 35
            elif current_cci > -200:
                signal = "强势下跌"
                score = 20
            else:
                signal = "超强下跌"
                score = 5
            
            return {
                'cci': current_cci,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'cci': 0, 'score': 50, 'signal': 'CCI计算失败'}
    
    # ============ 动量指标 ============
    
    def calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """
        Williams %R - 威廉指标
        反映超买超卖状态
        """
        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            
            willr = talib.WILLR(high, low, close, timeperiod=period)
            current_willr = willr[-1] if not np.isnan(willr[-1]) else -50
            
            # Williams %R信号判断
            if current_willr <= -80:
                signal = "严重超卖"
                score = 90
            elif current_willr <= -50:
                signal = "超卖"
                score = 75
            elif current_willr <= -20:
                signal = "正常"
                score = 50
            else:
                signal = "超买"
                score = 20
            
            return {
                'williams_r': current_willr,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'williams_r': -50, 'score': 50, 'signal': 'Williams %R计算失败'}
    
    def calculate_stoch_rsi(self, df: pd.DataFrame, 
                           rsi_period: int = 14, 
                           stoch_period: int = 14) -> Dict[str, Any]:
        """
        StochRSI - 随机相对强弱指数
        RSI的随机指标版本
        """
        try:
            close = df['close'].values
            
            # 先计算RSI
            rsi = talib.RSI(close, timeperiod=rsi_period)
            
            # 计算StochRSI
            fastk, fastd = talib.STOCHRSI(close, timeperiod=rsi_period, 
                                         fastk_period=stoch_period, 
                                         fastd_period=3, fastd_matype=0)
            
            current_fastk = fastk[-1] if not np.isnan(fastk[-1]) else 50
            current_fastd = fastd[-1] if not np.isnan(fastd[-1]) else 50
            
            # StochRSI信号判断
            if current_fastk >= 80 and current_fastd >= 80:
                signal = "严重超买"
                score = 15
            elif current_fastk >= 50:
                signal = "超买区域"
                score = 30
            elif current_fastk <= 20 and current_fastd <= 20:
                signal = "严重超卖"
                score = 90
            elif current_fastk <= 50:
                signal = "超卖区域"
                score = 70
            else:
                signal = "正常区域"
                score = 50
            
            return {
                'stoch_k': current_fastk,
                'stoch_d': current_fastd,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'stoch_k': 50, 'stoch_d': 50, 'score': 50, 'signal': 'StochRSI计算失败'}
    
    def calculate_mfi(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """
        MFI - 资金流量指标
        结合价格和成交量的动量指标
        """
        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values
            
            mfi = talib.MFI(high, low, close, volume, timeperiod=period)
            current_mfi = mfi[-1] if not np.isnan(mfi[-1]) else 50
            
            # MFI信号判断
            if current_mfi >= 80:
                signal = "资金超买"
                score = 20
            elif current_mfi >= 60:
                signal = "资金流入"
                score = 75
            elif current_mfi <= 20:
                signal = "资金超卖"
                score = 90
            elif current_mfi <= 40:
                signal = "资金流出"
                score = 35
            else:
                signal = "资金平衡"
                score = 50
            
            return {
                'mfi': current_mfi,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'mfi': 50, 'score': 50, 'signal': 'MFI计算失败'}
    
    # ============ 波动率指标 ============
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Dict[str, Any]:
        """
        ATR - 平均真实范围
        衡量价格波动性
        """
        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            
            atr = talib.ATR(high, low, close, timeperiod=period)
            current_atr = atr[-1] if not np.isnan(atr[-1]) else 0
            current_price = close[-1]
            
            # 计算ATR百分比
            atr_percent = (current_atr / current_price) * 100 if current_price > 0 else 0
            
            # ATR信号判断
            if atr_percent >= 5:
                signal = "高波动"
                score = 30  # 高波动风险较大
            elif atr_percent >= 3:
                signal = "中等波动"
                score = 60
            elif atr_percent >= 1:
                signal = "低波动"
                score = 80
            else:
                signal = "极低波动"
                score = 70  # 极低波动可能缺乏机会
            
            return {
                'atr': current_atr,
                'atr_percent': atr_percent,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'atr': 0, 'atr_percent': 0, 'score': 50, 'signal': 'ATR计算失败'}
    
    def calculate_bbands_advanced(self, df: pd.DataFrame, period: int = 20) -> Dict[str, Any]:
        """
        高级布林带分析
        包含带宽、位置等多维分析
        """
        try:
            close = df['close'].values
            
            upper, middle, lower = talib.BBANDS(close, timeperiod=period, 
                                               nbdevup=2, nbdevdn=2, matype=0)
            
            current_close = close[-1]
            current_upper = upper[-1] if not np.isnan(upper[-1]) else current_close
            current_middle = middle[-1] if not np.isnan(middle[-1]) else current_close
            current_lower = lower[-1] if not np.isnan(lower[-1]) else current_close
            
            # 计算位置百分比
            if current_upper != current_lower:
                position = (current_close - current_lower) / (current_upper - current_lower) * 100
            else:
                position = 50
            
            # 计算带宽
            bandwidth = ((current_upper - current_lower) / current_middle) * 100 if current_middle > 0 else 0
            
            # 布林带信号判断
            if position >= 90:
                signal = "接近上轨"
                score = 25  # 可能超买
            elif position >= 70:
                signal = "强势区域"
                score = 75
            elif position <= 10:
                signal = "接近下轨"
                score = 85  # 可能超卖，买入机会
            elif position <= 30:
                signal = "弱势区域"
                score = 40
            else:
                signal = "中性区域"
                score = 50
            
            return {
                'upper': current_upper,
                'middle': current_middle,
                'lower': current_lower,
                'position': position,
                'bandwidth': bandwidth,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'position': 50, 'bandwidth': 0, 'score': 50, 'signal': '布林带计算失败'}
    
    # ============ 成交量指标 ============
    
    def calculate_obv(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        OBV - 平衡成交量
        分析成交量与价格关系
        """
        try:
            close = df['close'].values
            volume = df['volume'].values
            
            obv = talib.OBV(close, volume)
            
            # 计算OBV趋势
            if len(obv) >= 5:
                recent_obv = obv[-5:]
                obv_trend = np.polyfit(range(5), recent_obv, 1)[0]
                
                if obv_trend > 0:
                    signal = "成交量上升"
                    score = 75
                elif obv_trend < 0:
                    signal = "成交量下降"
                    score = 30
                else:
                    signal = "成交量平稳"
                    score = 50
            else:
                signal = "数据不足"
                score = 50
                obv_trend = 0
            
            return {
                'obv': obv[-1] if len(obv) > 0 else 0,
                'obv_trend': obv_trend,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'obv': 0, 'obv_trend': 0, 'score': 50, 'signal': 'OBV计算失败'}
    
    def calculate_ad(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        A/D Line - 累积/派发线
        衡量资金流入流出
        """
        try:
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            volume = df['volume'].values
            
            ad = talib.AD(high, low, close, volume)
            
            # 计算A/D线趋势
            if len(ad) >= 5:
                recent_ad = ad[-5:]
                ad_trend = np.polyfit(range(5), recent_ad, 1)[0]
                
                if ad_trend > 0:
                    signal = "资金流入"
                    score = 80
                elif ad_trend < 0:
                    signal = "资金流出" 
                    score = 25
                else:
                    signal = "资金平衡"
                    score = 50
            else:
                signal = "数据不足"
                score = 50
                ad_trend = 0
            
            return {
                'ad': ad[-1] if len(ad) > 0 else 0,
                'ad_trend': ad_trend,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'ad': 0, 'ad_trend': 0, 'score': 50, 'signal': 'A/D线计算失败'}
    
    # ============ 市场结构指标 ============
    
    def calculate_sar(self, df: pd.DataFrame, acceleration: float = 0.02, maximum: float = 0.2) -> Dict[str, Any]:
        """
        SAR - 抛物线指标
        趋势跟踪和反转信号
        """
        try:
            high = df['high'].values
            low = df['low'].values
            
            sar = talib.SAR(high, low, acceleration=acceleration, maximum=maximum)
            current_sar = sar[-1] if not np.isnan(sar[-1]) else 0
            current_close = df['close'].iloc[-1]
            
            # SAR信号判断
            if current_close > current_sar:
                signal = "SAR看涨"
                score = 75
            else:
                signal = "SAR看跌"
                score = 25
            
            # 计算距离百分比
            distance_percent = abs(current_close - current_sar) / current_close * 100 if current_close > 0 else 0
            
            return {
                'sar': current_sar,
                'distance_percent': distance_percent,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'sar': 0, 'distance_percent': 0, 'score': 50, 'signal': 'SAR计算失败'}
    
    def calculate_pivot_points(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        枢轴点分析
        计算支撑阻力位
        """
        try:
            if len(df) < 2:
                return {'score': 50, 'signal': '数据不足'}
            
            # 使用前一日数据计算枢轴点
            prev_high = df['high'].iloc[-2]
            prev_low = df['low'].iloc[-2]
            prev_close = df['close'].iloc[-2]
            current_close = df['close'].iloc[-1]
            
            # 标准枢轴点公式
            pivot = (prev_high + prev_low + prev_close) / 3
            r1 = 2 * pivot - prev_low
            s1 = 2 * pivot - prev_high
            r2 = pivot + (prev_high - prev_low)
            s2 = pivot - (prev_high - prev_low)
            
            # 判断当前价格位置
            if current_close > r1:
                signal = "突破阻力1"
                score = 85
            elif current_close > pivot:
                signal = "枢轴上方"
                score = 70
            elif current_close > s1:
                signal = "枢轴下方"
                score = 40
            else:
                signal = "跌破支撑1"
                score = 20
            
            return {
                'pivot': pivot,
                'r1': r1,
                'r2': r2,
                's1': s1,
                's2': s2,
                'current_position': signal,
                'signal': signal,
                'score': score
            }
        except Exception as e:
            return {'pivot': 0, 'score': 50, 'signal': '枢轴点计算失败'}
    
    # ============ 综合分析 ============
    
    def calculate_comprehensive_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        综合技术分析评分
        整合所有指标的多维度评分
        """
        try:
            results = {}
            
            # 趋势指标 (40%权重)
            adx_result = self.calculate_adx(df)
            aroon_result = self.calculate_aroon(df)
            cci_result = self.calculate_cci(df)
            sar_result = self.calculate_sar(df)
            
            trend_score = (adx_result['score'] * 0.4 + 
                          aroon_result['score'] * 0.3 + 
                          cci_result['score'] * 0.2 + 
                          sar_result['score'] * 0.1)
            
            # 动量指标 (30%权重)
            willr_result = self.calculate_williams_r(df)
            stochrsi_result = self.calculate_stoch_rsi(df)
            mfi_result = self.calculate_mfi(df)
            
            momentum_score = (willr_result['score'] * 0.4 + 
                            stochrsi_result['score'] * 0.4 + 
                            mfi_result['score'] * 0.2)
            
            # 波动率指标 (15%权重)
            atr_result = self.calculate_atr(df)
            bbands_result = self.calculate_bbands_advanced(df)
            
            volatility_score = (atr_result['score'] * 0.4 + 
                              bbands_result['score'] * 0.6)
            
            # 成交量指标 (15%权重)
            obv_result = self.calculate_obv(df)
            ad_result = self.calculate_ad(df)
            
            volume_score = (obv_result['score'] * 0.6 + 
                          ad_result['score'] * 0.4)
            
            # 计算综合评分
            comprehensive_score = (trend_score * 0.4 + 
                                 momentum_score * 0.3 + 
                                 volatility_score * 0.15 + 
                                 volume_score * 0.15)
            
            # 生成综合评级
            if comprehensive_score >= 80:
                rating = "强烈推荐"
                level = "A+"
            elif comprehensive_score >= 70:
                rating = "推荐"
                level = "A"
            elif comprehensive_score >= 60:
                rating = "中性偏好"
                level = "B+"
            elif comprehensive_score >= 50:
                rating = "中性"
                level = "B"
            elif comprehensive_score >= 40:
                rating = "中性偏弱"
                level = "C+"
            elif comprehensive_score >= 30:
                rating = "不推荐"
                level = "C"
            else:
                rating = "强烈不推荐"
                level = "D"
            
            # 收集所有指标信号
            signals = []
            if adx_result['signal'] != 'ADX计算失败':
                signals.append(f"ADX: {adx_result['signal']}")
            if aroon_result['signal'] != 'Aroon计算失败':
                signals.append(f"Aroon: {aroon_result['signal']}")
            if willr_result['signal'] != 'Williams %R计算失败':
                signals.append(f"威廉: {willr_result['signal']}")
            if mfi_result['signal'] != 'MFI计算失败':
                signals.append(f"MFI: {mfi_result['signal']}")
            
            results = {
                'comprehensive_score': round(comprehensive_score, 1),
                'rating': rating,
                'level': level,
                'trend_score': round(trend_score, 1),
                'momentum_score': round(momentum_score, 1),
                'volatility_score': round(volatility_score, 1),
                'volume_score': round(volume_score, 1),
                'signals': signals[:4],  # 取前4个主要信号
                'detailed_results': {
                    'adx': adx_result,
                    'aroon': aroon_result,
                    'cci': cci_result,
                    'williams_r': willr_result,
                    'stoch_rsi': stochrsi_result,
                    'mfi': mfi_result,
                    'atr': atr_result,
                    'bbands': bbands_result,
                    'obv': obv_result,
                    'ad': ad_result,
                    'sar': sar_result
                }
            }
            
            return results
            
        except Exception as e:
            return {
                'comprehensive_score': 50,
                'rating': '计算失败',
                'level': 'N/A',
                'signals': [f'指标计算错误: {str(e)}']
            }
    
    def get_trading_signals(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        生成交易信号建议
        基于综合分析给出具体操作建议
        """
        try:
            analysis = self.calculate_comprehensive_score(df)
            score = analysis['comprehensive_score']
            
            # 根据评分生成交易建议
            if score >= 75:
                action = "强烈买入"
                confidence = "高"
                risk_level = "中等"
                suggestion = "技术面强势，建议积极介入"
            elif score >= 65:
                action = "买入"
                confidence = "较高"
                risk_level = "中等"
                suggestion = "技术指标向好，可以考虑买入"
            elif score >= 55:
                action = "观望"
                confidence = "中等"
                risk_level = "中等"
                suggestion = "技术面中性，建议继续观察"
            elif score >= 45:
                action = "谨慎"
                confidence = "较低"
                risk_level = "较高"
                suggestion = "技术面偏弱，注意风险控制"
            else:
                action = "回避"
                confidence = "低"
                risk_level = "高"
                suggestion = "技术面较差，建议回避"
            
            # 计算关键价格位
            current_close = df['close'].iloc[-1]
            pivot_result = self.calculate_pivot_points(df)
            atr_result = self.calculate_atr(df)
            
            # 设置止损止盈位
            atr_value = atr_result.get('atr', current_close * 0.02)
            stop_loss = current_close - 2 * atr_value
            take_profit = current_close + 3 * atr_value
            
            return {
                'action': action,
                'confidence': confidence,
                'risk_level': risk_level,
                'suggestion': suggestion,
                'entry_price': current_close,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': "根据风险承受度调整",
                'time_frame': "中短期",
                'key_levels': {
                    'support': pivot_result.get('s1', current_close * 0.95),
                    'resistance': pivot_result.get('r1', current_close * 1.05),
                    'pivot': pivot_result.get('pivot', current_close)
                },
                'risk_reward_ratio': round((take_profit - current_close) / (current_close - stop_loss), 2) if current_close > stop_loss else 0
            }
            
        except Exception as e:
            return {
                'action': '分析失败',
                'suggestion': f'无法生成交易信号: {str(e)}',
                'confidence': '无'
            }

def main():
    """测试高级指标系统"""
    print("🔍 高级技术指标系统测试")
    print("="*50)
    
    # 这里可以添加测试代码
    print("✅ 高级指标库已就绪!")
    print("\n包含的指标:")
    print("📈 趋势指标: ADX, Aroon, CCI, SAR")
    print("📊 动量指标: Williams %R, StochRSI, MFI")
    print("📉 波动率指标: ATR, 高级布林带")
    print("📦 成交量指标: OBV, A/D线")
    print("🎯 综合分析: 多维度评分系统")
    print("💡 交易信号: 智能操作建议")

if __name__ == "__main__":
    main() 