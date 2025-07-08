#!/usr/bin/env python3
"""
测试邮件发送功能
"""

from core.email_sender import send_notification_email

# 测试配置 - QQ邮箱
test_config = {
    'enabled': True,
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 587,  # 使用TLS端口
    'username': '844497109@qq.com',  # 发送邮箱
    'password': 'ktnuezzpjgvsbbee',    # QQ邮箱授权码
    'to_email': '844497109@qq.com',       # 接收邮箱
    'use_tls': True,  # 使用TLS加密
    'subject_template': '📈 测试邮件 - {date}'
}

def test_email():
    """测试邮件发送"""
    print("📧 开始测试邮件发送...")
    print(f"发送邮箱: {test_config['username']}")
    print(f"接收邮箱: {test_config['to_email']}")
    print(f"SMTP配置: {test_config['smtp_server']}:{test_config['smtp_port']}")
    
    # 使用之前创建的测试结果文件
    results_file = 'results/test_selection_2025-07-08.json'
    
    success = send_notification_email(
        strategy_name='comprehensive',
        results_file=results_file,
        config=test_config
    )
    
    if success:
        print("✅ 邮件发送测试成功！")
        print("请检查 844497109@qq.com 邮箱，查看是否收到测试邮件")
    else:
        print("❌ 邮件发送测试失败！")
        print("请检查：")
        print("1. 邮箱配置是否正确")
        print("2. 应用密码是否正确（Gmail需要使用应用专用密码）")
        print("3. 网络连接是否正常")

if __name__ == "__main__":
    test_email() 