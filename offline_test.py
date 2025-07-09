#!/usr/bin/env python3
"""
Offline Test Script
-------------------
在不调用任何外部股票数据 API 的情况下：
1. 生成示例选股结果 JSON 文件
2. 调用 WxPusher 测试微信推送功能
3. 用于 GitHub Actions 环境验证
不影响线上真实功能。
"""

import os
import json
from datetime import datetime
from core.wxpusher_sender import WxPusherSender

DUMMY_STOCKS = [
    {
        "code": "000001",
        "name": "平安银行",
        "score": 88,
        "current_price": 12.34,
        "market_cap": 123_000_000_000,
        "reasons": ["示例数据", "技术指标优秀"]
    },
    {
        "code": "600036",
        "name": "招商银行",
        "score": 83,
        "current_price": 34.56,
        "market_cap": 456_000_000_000,
        "reasons": ["示例数据", "基本面稳健"]
    }
]


def create_dummy_results(strategy: str) -> str:
    """生成示例结果文件并返回路径"""
    os.makedirs("results", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    results_file = f"results/{strategy}_selection_{today}.json"

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(DUMMY_STOCKS, f, ensure_ascii=False, indent=2)

    print(f"✅ 已生成示例结果文件: {results_file}")
    return results_file


def main():
    strategy = os.environ.get("TEST_STRATEGY", "comprehensive")
    results_path = create_dummy_results(strategy)

    # 初始化WxPusher发送器
    sender = WxPusherSender()
    if not sender.is_enabled():
        print("❌ WxPusher未启用，跳过微信推送")
        return

    # 读取生成的测试数据
    with open(results_path, 'r', encoding='utf-8') as f:
        stocks = json.load(f)

    # 发送微信推送
    today = datetime.now().strftime('%Y-%m-%d')
    success = sender.send_stock_selection_notification(
        stocks=stocks,
        strategy_name=strategy,
        date=today
    )

    if success:
        print("🎉 微信推送发送成功！")
    else:
        print("⚠️ 微信推送发送失败！")


if __name__ == "__main__":
    main() 