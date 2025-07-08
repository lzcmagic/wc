#!/usr/bin/env python3
"""
测试配置加载脚本
用于验证user_config.py是否正确加载
"""

import os
import sys

def test_config_loading():
    """测试配置加载"""
    print("🔍 测试配置加载...")
    
    # 创建测试配置
    test_config = '''USER_CONFIG = {
    'EMAIL_CONFIG': {
        'enabled': True,
        'smtp_server': 'smtp.qq.com',
        'smtp_port': 465,
        'username': 'test@qq.com',
        'password': 'test_password',
        'to_email': 'test@example.com',
        'use_tls': False,
        'subject_template': '📈 测试邮件 - {date}'
    }
}
'''
    
    # 写入测试配置文件
    with open('user_config.py', 'w', encoding='utf-8') as f:
        f.write(test_config)
    
    print("✅ 创建测试配置文件: user_config.py")
    
    try:
        # 导入配置
        from core.config import config
        
        print("✅ 成功导入配置模块")
        print(f"邮件配置: {config.EMAIL_CONFIG}")
        
        # 检查配置
        email_config = config.EMAIL_CONFIG
        if email_config.get('enabled'):
            print("✅ 邮件通知已启用")
        else:
            print("❌ 邮件通知未启用")
            
        if email_config.get('username') and email_config.get('password'):
            print("✅ 用户名和密码已配置")
        else:
            print("❌ 用户名或密码未配置")
            
        print(f"SMTP服务器: {email_config.get('smtp_server')}")
        print(f"SMTP端口: {email_config.get('smtp_port')}")
        print(f"使用TLS: {email_config.get('use_tls')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    finally:
        # 清理测试文件
        if os.path.exists('user_config.py'):
            os.remove('user_config.py')
            print("🧹 清理测试配置文件")

if __name__ == "__main__":
    success = test_config_loading()
    if success:
        print("\n🎉 配置加载测试通过！")
    else:
        print("\n❌ 配置加载测试失败！")
        sys.exit(1) 