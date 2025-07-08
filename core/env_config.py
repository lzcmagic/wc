"""
环境配置管理模块
支持本地 .env 文件和 GitHub Actions 环境变量
"""

import os
from typing import Optional, Dict, Any

try:
    from dotenv import load_dotenv
    load_dotenv()  # 自动加载 .env 文件
except ImportError:
    print("⚠️ python-dotenv 未安装，无法加载 .env 文件")

class EnvironmentConfig:
    """环境配置管理器"""
    
    def __init__(self):
        self._cache = {}
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔类型环境变量"""
        value = os.getenv(key, str(default)).lower()
        return value in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数类型环境变量"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default
    
    def get_str(self, key: str, default: str = '') -> str:
        """获取字符串类型环境变量"""
        return os.getenv(key, default)
    
    def get_email_config(self) -> Dict[str, Any]:
        """获取邮件配置"""
        if 'email_config' in self._cache:
            return self._cache['email_config']
            
        config = {
            'enabled': self.get_bool('EMAIL_ENABLED', False),
            'smtp_server': self.get_str('EMAIL_SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': self.get_int('EMAIL_SMTP_PORT', 587),
            'use_tls': self.get_bool('EMAIL_USE_TLS', True),
            'username': self.get_str('EMAIL_USERNAME', ''),
            'password': self.get_str('EMAIL_PASSWORD', ''),
            'to_email': self.get_str('EMAIL_TO', ''),
            'subject_template': self.get_str('EMAIL_SUBJECT_TEMPLATE', '📈 每日选股推荐 - {date}'),
        }
        
        # 缓存配置
        self._cache['email_config'] = config
        return config
    
    def validate_email_config(self) -> bool:
        """验证邮件配置是否完整"""
        config = self.get_email_config()
        
        if not config['enabled']:
            return True  # 如果未启用，则认为配置有效
            
        required_fields = ['username', 'password', 'to_email']
        missing_fields = [field for field in required_fields if not config[field]]
        
        if missing_fields:
            print(f"❌ 邮件配置不完整，缺少字段: {', '.join(missing_fields)}")
            return False
            
        return True
    
    def print_config_status(self):
        """打印配置状态"""
        email_config = self.get_email_config()
        
        print("📧 邮件配置状态:")
        print(f"   启用状态: {'✅ 已启用' if email_config['enabled'] else '❌ 已禁用'}")
        print(f"   SMTP服务器: {email_config['smtp_server']}:{email_config['smtp_port']}")
        print(f"   使用TLS: {'是' if email_config['use_tls'] else '否'}")
        print(f"   发送邮箱: {'已配置' if email_config['username'] else '未配置'}")
        print(f"   接收邮箱: {'已配置' if email_config['to_email'] else '未配置'}")
        print(f"   密码: {'已配置' if email_config['password'] else '未配置'}")
        
        if email_config['enabled'] and not self.validate_email_config():
            print("❌ 邮件配置不完整，请检查环境变量或 .env 文件")
        elif email_config['enabled']:
            print("✅ 邮件配置完整")

# 全局环境配置实例
env_config = EnvironmentConfig() 