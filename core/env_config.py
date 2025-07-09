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
    


    def get_wxpusher_config(self) -> Dict[str, Any]:
        """获取WxPusher微信推送配置"""
        if 'wxpusher_config' in self._cache:
            return self._cache['wxpusher_config']

        # 处理UID列表
        uids_str = self.get_str('WXPUSHER_UIDS', '')
        uids = [uid.strip() for uid in uids_str.split(',') if uid.strip()] if uids_str else []

        # 处理主题ID列表
        topic_ids_str = self.get_str('WXPUSHER_TOPIC_IDS', '')
        topic_ids = []
        if topic_ids_str:
            for tid in topic_ids_str.split(','):
                tid = tid.strip()
                if tid.isdigit():
                    topic_ids.append(int(tid))

        config = {
            'enabled': self.get_bool('WXPUSHER_ENABLED', False),
            'app_token': self.get_str('WXPUSHER_APP_TOKEN', ''),
            'uids': uids,
            'topic_ids': topic_ids,
            'spt': self.get_str('WXPUSHER_SPT', ''),  # 极简推送token
        }

        # 缓存配置
        self._cache['wxpusher_config'] = config
        return config
    


    def validate_wxpusher_config(self) -> bool:
        """验证WxPusher配置是否完整"""
        config = self.get_wxpusher_config()

        if not config['enabled']:
            return True  # 如果未启用，则认为配置有效

        # 检查APP_TOKEN
        if not config['app_token']:
            print("❌ WxPusher配置不完整，缺少 WXPUSHER_APP_TOKEN")
            return False

        # 检查是否有推送目标（UID或主题ID）
        if not config['uids'] and not config['topic_ids']:
            print("❌ WxPusher配置不完整，需要至少配置 WXPUSHER_UIDS 或 WXPUSHER_TOPIC_IDS")
            return False

        return True
    
    def print_config_status(self):
        """打印配置状态"""
        wxpusher_config = self.get_wxpusher_config()

        print("📱 WxPusher微信推送配置状态:")
        print(f"   启用状态: {'✅ 已启用' if wxpusher_config['enabled'] else '❌ 已禁用'}")
        print(f"   APP_TOKEN: {'已配置' if wxpusher_config['app_token'] else '未配置'}")
        print(f"   推送用户: {len(wxpusher_config['uids'])} 个UID")
        print(f"   推送主题: {len(wxpusher_config['topic_ids'])} 个主题")
        print(f"   极简推送: {'已配置' if wxpusher_config['spt'] else '未配置'}")

        if wxpusher_config['enabled'] and not self.validate_wxpusher_config():
            print("❌ WxPusher配置不完整，请检查环境变量或 .env 文件")
        elif wxpusher_config['enabled']:
            print("✅ WxPusher配置完整")

# 全局环境配置实例
env_config = EnvironmentConfig() 