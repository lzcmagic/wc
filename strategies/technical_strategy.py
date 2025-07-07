from core.base_selector import BaseSelector

class TechnicalStrategy(BaseSelector):
    def __init__(self):
        super().__init__('technical')

    def _apply_strategy(self, data):
        """
        应用技术分析策略为单只股票评分。
        :param data: 包含指标的DataFrame
        :return: (score, reasons) 元组
        """
        score = 0
        reasons = []
        
        # 使用 .iloc[-1] 获取最新的数据行
        latest = data.iloc[-1]

        # 均线多头排列
        if latest['SMA_5'] > latest['SMA_10'] > latest['SMA_20']:
            score += 30
            reasons.append(f"均线多头(5>10>20)")
        
        # MACD 金叉
        if latest['MACD_12_26_9'] > latest['MACDs_12_26_9'] and data.iloc[-2]['MACD_12_26_9'] < data.iloc[-2]['MACDs_12_26_9']:
            score += 30
            reasons.append("MACD金叉")
            
        # RSI 低位
        if latest['RSI_14'] < 40:
            score += 20
            reasons.append(f"RSI({latest['RSI_14']:.1f})低位")
            
        # KDJ 金叉
        if latest['KDJk_9_3_3'] > latest['KDJd_9_3_3'] and data.iloc[-2]['KDJk_9_3_3'] < data.iloc[-2]['KDJd_9_3_3']:
            score += 20
            reasons.append("KDJ金叉")
            
        return score, reasons 