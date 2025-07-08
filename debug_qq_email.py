#!/usr/bin/env python3
"""
调试QQ邮箱连接问题
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_connection():
    """测试SMTP连接"""
    print("🔍 开始调试QQ邮箱连接...")
    
    # 配置
    smtp_server = 'smtp.qq.com'
    port_587 = 587
    port_465 = 465
    username = '844497109@qq.com'
    password = 'ktnuezzpjgvsbbee'
    
    print(f"📧 邮箱: {username}")
    print(f"🔑 授权码: {password[:4]}****{password[-4:]}")
    
    # 测试587端口
    print(f"\n🔌 测试端口 {port_587} (TLS)...")
    try:
        server = smtplib.SMTP(smtp_server, port_587, timeout=10)
        print("✅ SMTP连接成功")
        
        server.starttls()
        print("✅ TLS握手成功")
        
        server.login(username, password)
        print("✅ 登录成功")
        
        server.quit()
        print("✅ 587端口测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 587端口测试失败: {e}")
    
    # 测试465端口
    print(f"\n🔌 测试端口 {port_465} (SSL)...")
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(smtp_server, port_465, context=context, timeout=10)
        print("✅ SSL连接成功")
        
        server.login(username, password)
        print("✅ 登录成功")
        
        server.quit()
        print("✅ 465端口测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 465端口测试失败: {e}")
    
    return False

def test_send_simple_email():
    """测试发送简单邮件"""
    print(f"\n📤 测试发送简单邮件...")
    
    try:
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = '844497109@qq.com'
        msg['To'] = 'l1396448080@gmail.com'
        msg['Subject'] = '测试QQ邮箱发送'
        
        body = "这是一封测试邮件，用于验证QQ邮箱SMTP配置。"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 发送邮件
        server = smtplib.SMTP_SSL('smtp.qq.com', 465, timeout=10)
        server.login('844497109@qq.com', 'ktnuezzpjgvsbbee')
        
        text = msg.as_string()
        server.sendmail('844497109@qq.com', 'l1396448080@gmail.com', text)
        server.quit()
        
        print("✅ 简单邮件发送成功！")
        return True
        
    except Exception as e:
        print(f"❌ 简单邮件发送失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 QQ邮箱连接调试工具")
    print("=" * 50)
    
    # 测试连接
    connection_ok = test_smtp_connection()
    
    if connection_ok:
        # 测试发送
        test_send_simple_email()
    else:
        print("\n💡 建议检查：")
        print("1. QQ邮箱是否开启了SMTP服务")
        print("2. 授权码是否正确")
        print("3. 网络环境是否有限制")
        print("4. 尝试在GitHub Actions中测试") 