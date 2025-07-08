import json

with open('results/test_selection_2025-07-08.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
 
print("测试选股结果内容：")
for stock in data:
    print(f"代码: {stock['code']}, 名称: {stock['name']}, 得分: {stock['score']}, 推荐理由: {' | '.join(stock['reasons'])}, 价格: {stock['price']}, 市值(亿): {stock['market_cap']}") 