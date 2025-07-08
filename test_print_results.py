#!/usr/bin/env python3
"""
测试 print_results 方法是否能正确处理修复后的数据结构
"""

from core.base_selector import BaseSelector

# 创建测试数据，模拟修复后的数据结构
test_stocks = [
    {
        'code': '000001',
        'name': '平安银行',
        'score': 85.5,
        'reasons': ['综合评分优秀', '技术形态良好'],
        'price': 12.34,
        'market_cap': 150.2
    },
    {
        'code': '000002',
        'name': '万科A',
        'score': 82.1,
        'reasons': ['基本面稳健'],
        'price': 18.56,
        'market_cap': 200.8
    }
]

# 创建一个简单的测试类
class TestSelector(BaseSelector):
    def __init__(self):
        super().__init__('comprehensive')  # 使用有效的策略名称
    
    def print_results(self, stocks):
        super().print_results(stocks)

# 测试
if __name__ == "__main__":
    print("测试 print_results 方法...")
    selector = TestSelector()
    
    try:
        selector.print_results(test_stocks)
        print("✅ print_results 测试通过！")
    except Exception as e:
        print(f"❌ print_results 测试失败: {e}")
        import traceback
        traceback.print_exc() 