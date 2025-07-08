#!/usr/bin/env python3
"""
邮件通知发送脚本
用于在GitHub Action中发送选股结果邮件
"""

import os
import sys
import json
from datetime import datetime
from core.email_sender import send_notification_email
from core.env_config import env_config

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python send_email_notification.py <strategy_name> [results_file]")
        print("示例: python send_email_notification.py comprehensive")
        print("示例: python send_email_notification.py technical results/technical_selection_2025-07-08.json")
        sys.exit(1)
    
    strategy_name = sys.argv[1]
    
    # 如果没有指定结果文件，则自动查找
    if len(sys.argv) >= 3:
        results_file = sys.argv[2]
    else:
        # 自动查找当天的结果文件
        today = datetime.now().strftime('%Y-%m-%d')
        results_file = f"results/{strategy_name}_selection_{today}.json"
    
    print(f"📧 准备发送邮件通知...")
    print(f"   策略: {strategy_name}")
    print(f"   结果文件: {results_file}")
    
    # 检查邮件配置
    email_config = env_config.get_email_config()
    if not email_config.get('enabled', False):
        print("❌ 邮件通知已禁用，请在配置中启用")
        sys.exit(1)
    
    if not env_config.validate_email_config():
        print("❌ 邮件配置不完整，请检查环境变量或 .env 文件")
        sys.exit(1)
    
    # 发送邮件
    success = send_notification_email(
        strategy_name=strategy_name,
        results_file=results_file,
        config=email_config
    )
    
    if success:
        print("✅ 邮件发送成功！")
        sys.exit(0)
    else:
        print("❌ 邮件发送失败！")
        sys.exit(1)

if __name__ == "__main__":
    main() 