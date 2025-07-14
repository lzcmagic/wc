#!/usr/bin/env python3
"""
WxPusher微信推送通知发送脚本
用于在GitHub Action中发送选股结果微信推送
替换原有的邮件通知功能
"""

import os
import sys
import json
import hashlib
from datetime import datetime, timedelta
from core.wxpusher_sender import WxPusherSender
from core.env_config import env_config

def get_cache_file(strategy_name, date):
    """获取缓存文件路径"""
    cache_dir = "results/.cache"
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, f"push_cache_{strategy_name}_{date}")

def is_already_sent(strategy_name, results_content, date):
    """检查是否已经发送过相同内容"""
    cache_file = get_cache_file(strategy_name, date)
    
    if not os.path.exists(cache_file):
        return False
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        # 检查时间（2小时内算重复）
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        if datetime.now() - cache_time > timedelta(hours=2):
            return False
        
        # 检查内容哈希
        content_hash = hashlib.md5(results_content.encode()).hexdigest()
        return cache_data.get('content_hash') == content_hash
        
    except Exception:
        return False

def mark_as_sent(strategy_name, results_content, date):
    """标记为已发送"""
    cache_file = get_cache_file(strategy_name, date)
    content_hash = hashlib.md5(results_content.encode()).hexdigest()
    
    cache_data = {
        'timestamp': datetime.now().isoformat(),
        'content_hash': content_hash,
        'strategy': strategy_name,
        'date': date
    }
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python send_wxpush_notification.py <strategy_name> [results_file]")
        print("示例: python send_wxpush_notification.py comprehensive")
        print("示例: python send_wxpush_notification.py technical results/technical_selection_2025-07-08.json")
        sys.exit(1)
    
    strategy_name = sys.argv[1]
    
    # 如果没有指定结果文件，则自动查找
    if len(sys.argv) >= 3:
        results_file = sys.argv[2]
    else:
        # 自动查找当天的结果文件
        today = datetime.now().strftime('%Y-%m-%d')
        results_file = f"results/{strategy_name}_selection_{today}.json"
    
    print(f"📱 准备发送微信推送通知...")
    print(f"   策略: {strategy_name}")
    print(f"   结果文件: {results_file}")
    
    # 检查结果文件是否存在
    if not os.path.exists(results_file):
        print(f"⚠️ 结果文件不存在: {results_file}")
        print("📱 可能是没有找到符合条件的股票，发送无结果通知...")

        # 发送无结果通知
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 检查重复推送
            no_result_content = f"no_results_{strategy_name}_{today}"
            if is_already_sent(strategy_name, no_result_content, today):
                print("⚠️ 检测到2小时内已发送过相同的无结果通知，跳过重复推送")
                sys.exit(0)
            
            sender = WxPusherSender()
            if sender.is_enabled():
                success = sender.send_no_results_notification(strategy_name, today)
                if success:
                    mark_as_sent(strategy_name, no_result_content, today)
                    print("✅ 无结果通知发送成功！")
                    sys.exit(0)
                else:
                    print("❌ 无结果通知发送失败！")
                    sys.exit(1)
            else:
                print("❌ WxPusher未启用，无法发送通知")
                sys.exit(1)
        except Exception as e:
            print(f"❌ 发送无结果通知时出错: {e}")
            sys.exit(1)
    
    # 读取选股结果
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            content = f.read()
            stocks = json.loads(content)
        
        if not stocks:
            print("⚠️ 选股结果为空，跳过推送")
            sys.exit(0)
            
        print(f"📊 读取到 {len(stocks)} 只股票")
        
        # 检查重复推送
        today = datetime.now().strftime('%Y-%m-%d')
        if is_already_sent(strategy_name, content, today):
            print("⚠️ 检测到2小时内已发送过相同内容，跳过重复推送")
            sys.exit(0)
        
    except Exception as e:
        print(f"❌ 读取结果文件失败: {e}")
        sys.exit(1)
    
    # 初始化WxPusher发送器
    try:
        sender = WxPusherSender()
        
        if not sender.is_enabled():
            print("❌ WxPusher未启用或配置不完整")
            print("💡 请检查WxPusher配置:")
            print("   - 确保已设置正确的APP_TOKEN和TOPIC_ID")
            print("   - 或者配置极简推送SPT")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ WxPusher初始化失败: {e}")
        sys.exit(1)
    
    # 发送选股结果通知
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        success = sender.send_stock_selection_notification(
            stocks=stocks,
            strategy_name=strategy_name,
            date=today
        )
        
        if success:
            mark_as_sent(strategy_name, content, today)
            print("✅ 微信推送发送成功！")
            print("📱 请检查您的微信，查看选股结果推送")
            sys.exit(0)
        else:
            print("❌ 微信推送发送失败！")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ 发送微信推送时出错: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
