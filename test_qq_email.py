#!/usr/bin/env python3
"""
测试QQ邮箱配置
"""

from core.email_sender import send_notification_email

# QQ邮箱测试配置
qq_config = {
    'enabled': True,
    'smtp_server': 'smtp.qq.com',
    'smtp_port': 465,  # 使用SSL端口
    'username': '844497109@qq.com',  # 发送邮箱
    'password': 'ktnuezzpjgvsbbee',    # QQ邮箱授权码
    'to_email': 'l1396448080@gmail.com',       # 接收邮箱
    'use_tls': False,  # SSL模式下不使用TLS
    'subject_template': '📈 QQ邮箱测试 - {date}'
}

def test_qq_email():
    """测试QQ邮箱发送"""
    print("📧 开始测试QQ邮箱发送...")
    print(f"发送邮箱: {qq_config['username']}")
    print(f"接收邮箱: {qq_config['to_email']}")
    print(f"SMTP配置: {qq_config['smtp_server']}:{qq_config['smtp_port']}")
    print(f"使用TLS: {qq_config['use_tls']}")
    
    # 使用之前创建的测试结果文件
    results_file = 'results/test_selection_2025-07-08.json'
    
    success = send_notification_email(
        strategy_name='comprehensive',
        results_file=results_file,
        config=qq_config
    )
    
    if success:
        print("✅ QQ邮箱发送测试成功！")
        print("请检查 l1396448080@gmail.com 邮箱，查看是否收到测试邮件")
    else:
        print("❌ QQ邮箱发送测试失败！")
        print("请检查：")
        print("1. QQ邮箱授权码是否正确")
        print("2. 是否开启了SMTP服务")
        print("3. 网络连接是否正常")
        print("4. 如果587端口失败，可以尝试465端口")

if __name__ == "__main__":
    test_qq_email() 