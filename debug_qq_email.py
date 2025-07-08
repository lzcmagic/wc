#!/usr/bin/env python3
"""
QQ邮箱调试脚本 - 详细诊断版本
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def test_smtp_connection(config):
    """测试SMTP连接"""
    print(f"🔍 开始SMTP连接测试...")
    print(f"服务器: {config['smtp_server']}")
    print(f"端口: {config['smtp_port']}")
    print(f"用户名: {config['username']}")
    print(f"密码长度: {len(config['password']) if config['password'] else 0}")
    print(f"接收邮箱: {config['to_email']}")
    print(f"使用TLS: {config['use_tls']}")
    
    try:
        # 测试连接
        if config['smtp_port'] == 465:
            print("📡 尝试SSL连接...")
            server = smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port'])
            print("✅ SSL连接成功")
        else:
            print("📡 尝试TLS连接...")
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config['use_tls']:
                server.starttls()
                print("✅ TLS连接成功")
        
        # 测试登录
        print("🔐 尝试登录...")
        server.login(config['username'], config['password'])
        print("✅ 登录成功")
        
        # 测试发送
        print("📧 尝试发送测试邮件...")
        msg = MIMEMultipart()
        msg['From'] = config['username']
        msg['To'] = config['to_email']
        msg['Subject'] = '🔧 QQ邮箱连接测试'
        
        body = f"""
        <html>
        <body>
            <h2>QQ邮箱连接测试成功！</h2>
            <p>时间: {os.popen('date').read().strip()}</p>
            <p>服务器: {config['smtp_server']}:{config['smtp_port']}</p>
            <p>连接方式: {'SSL' if config['smtp_port'] == 465 else 'TLS'}</p>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server.send_message(msg)
        print("✅ 测试邮件发送成功")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ 认证失败: {e}")
        print("可能原因:")
        print("1. 用户名或密码错误")
        print("2. 授权码已过期")
        print("3. 未开启SMTP服务")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ 连接失败: {e}")
        print("可能原因:")
        print("1. 网络连接问题")
        print("2. 防火墙阻止")
        print("3. 服务器地址或端口错误")
        return False
        
    except smtplib.SMTPException as e:
        print(f"❌ SMTP错误: {e}")
        return False
        
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False

def main():
    """主函数"""
    print("🚀 QQ邮箱调试工具")
    print("=" * 50)
    
    # 检查环境变量
    print("📋 环境变量检查:")
    email_username = os.getenv('EMAIL_USERNAME', '')
    email_password = os.getenv('EMAIL_PASSWORD', '')
    email_to = os.getenv('EMAIL_TO', '')
    
    print(f"EMAIL_USERNAME: {'已设置' if email_username else '未设置'}")
    print(f"EMAIL_PASSWORD: {'已设置' if email_password else '未设置'}")
    print(f"EMAIL_TO: {'已设置' if email_to else '未设置'}")
    
    if not all([email_username, email_password, email_to]):
        print("\n❌ 环境变量未完全设置！")
        print("请在GitHub Secrets中设置以下变量:")
        print("- EMAIL_USERNAME: QQ邮箱地址")
        print("- EMAIL_PASSWORD: QQ邮箱授权码")
        print("- EMAIL_TO: 接收邮箱地址")
        return
    
    # 测试配置
    config = {
        'smtp_server': 'smtp.qq.com',
        'smtp_port': 465,
        'username': email_username,
        'password': email_password,
        'to_email': email_to,
        'use_tls': False
    }
    
    print("\n" + "=" * 50)
    success = test_smtp_connection(config)
    
    if success:
        print("\n🎉 所有测试通过！QQ邮箱配置正确。")
    else:
        print("\n💡 故障排除建议:")
        print("1. 检查QQ邮箱是否开启SMTP服务")
        print("2. 确认授权码是否正确且未过期")
        print("3. 检查网络连接")
        print("4. 尝试使用587端口+TLS")

if __name__ == "__main__":
    main() 