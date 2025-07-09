#!/usr/bin/env python3
"""
WxPusher微信推送发送器
集成到选股系统中，用于发送选股结果通知
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .wxpusher_client import WxPusherClient, WxPusherSimpleClient
from .env_config import env_config

logger = logging.getLogger(__name__)


class WxPusherSender:
    """WxPusher微信推送发送器"""
    
    def __init__(self):
        """初始化WxPusher发送器"""
        # 硬编码配置
        self.config = {
            'enabled': True,
            'app_token': 'AT_fWXnH05M1MD8wFunlBRioiFtW5JL5yGm',
            'uids': [],  # 不使用UID推送
            'topic_ids': [41366],  # 使用主题推送
            'spt': ''  # 不使用极简推送
        }
        self.client = None
        self.simple_client = None

        if self.config['enabled']:
            self._init_clients()
    
    def _init_clients(self):
        """初始化推送客户端"""
        try:
            # 标准推送客户端
            if self.config['app_token']:
                self.client = WxPusherClient(self.config['app_token'])
                logger.info("✅ WxPusher标准推送客户端初始化成功")
            
            # 极简推送客户端
            if self.config['spt']:
                self.simple_client = WxPusherSimpleClient(self.config['spt'])
                logger.info("✅ WxPusher极简推送客户端初始化成功")
                
        except Exception as e:
            logger.error(f"❌ WxPusher客户端初始化失败: {e}")
    
    def is_enabled(self) -> bool:
        """检查WxPusher是否已启用"""
        return self.config['enabled'] and (self.client is not None or self.simple_client is not None)
    
    def send_stock_selection_notification(self, 
                                        stocks: List[Dict], 
                                        strategy_name: str,
                                        date: Optional[str] = None) -> bool:
        """
        发送选股结果通知
        
        Args:
            stocks: 选股结果列表
            strategy_name: 策略名称
            date: 选股日期
            
        Returns:
            是否发送成功
        """
        if not self.is_enabled():
            logger.info("📱 WxPusher未启用，跳过微信推送")
            return True
        
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        success = True
        
        # 标准推送
        if self.client and (self.config['uids'] or self.config['topic_ids']):
            try:
                result = self.client.send_stock_selection_result(
                    stocks=stocks,
                    strategy_name=strategy_name,
                    uids=self.config['uids'] if self.config['uids'] else None,
                    topic_ids=self.config['topic_ids'] if self.config['topic_ids'] else None,
                    date=date
                )
                
                if result.get('code') == 1000:
                    logger.info(f"✅ WxPusher标准推送发送成功")
                else:
                    logger.error(f"❌ WxPusher标准推送发送失败: {result.get('msg')}")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ WxPusher标准推送发送异常: {e}")
                success = False
        
        # 极简推送
        if self.simple_client:
            try:
                # 构建简单的文本消息
                content = self._build_simple_message(stocks, strategy_name, date)
                summary = f"{strategy_name}选股({len(stocks)}只)"
                
                result = self.simple_client.send_message(
                    content=content,
                    content_type=1,  # 文本格式
                    summary=summary
                )
                
                if result.get('code') == 1000:
                    logger.info(f"✅ WxPusher极简推送发送成功")
                else:
                    logger.error(f"❌ WxPusher极简推送发送失败: {result.get('msg')}")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ WxPusher极简推送发送异常: {e}")
                success = False
        
        return success
    
    def _build_simple_message(self, stocks: List[Dict], strategy_name: str, date: str) -> str:
        """构建极简推送的文本消息"""
        message = f"🎯 {strategy_name}策略选股结果\n"
        message += f"📅 日期: {date}\n"
        message += f"📊 选中股票: {len(stocks)} 只\n"
        message += "=" * 30 + "\n"
        
        if not stocks:
            message += "今日暂无符合条件的股票\n"
        else:
            for i, stock in enumerate(stocks[:5], 1):  # 限制显示前5只
                code = stock.get('code', 'N/A')
                name = stock.get('name', 'N/A')
                score = stock.get('score', 0)
                current_price = stock.get('current_price', 0)
                change_pct = stock.get('change_pct', 0)
                
                change_text = f"{change_pct:+.2f}%" if change_pct != 0 else "0.00%"
                message += f"{i}. {name}({code})\n"
                message += f"   💰 {current_price:.2f}元 {change_text}\n"
                message += f"   ⭐ {score:.1f}分\n"
            
            if len(stocks) > 5:
                message += f"... 还有 {len(stocks) - 5} 只股票\n"
        
        message += "=" * 30 + "\n"
        message += "⚠️ 本信息仅供参考，不构成投资建议\n"
        message += "🤖 由A股智能选股系统自动生成"
        
        return message
    
    def send_test_message(self) -> bool:
        """发送测试消息"""
        if not self.is_enabled():
            logger.warning("📱 WxPusher未启用，无法发送测试消息")
            return False
        
        test_content = """
        <h2>🧪 WxPusher测试消息</h2>
        <p><strong>📅 时间:</strong> {}</p>
        <p><strong>🎯 目的:</strong> 验证WxPusher推送功能</p>
        <hr/>
        <p style='color: #00aa00;'>✅ 如果您收到此消息，说明WxPusher配置正确！</p>
        <p style='color: #999; font-size: 12px;'>🤖 由A股智能选股系统发送</p>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        success = True
        
        # 标准推送测试
        if self.client and (self.config['uids'] or self.config['topic_ids']):
            try:
                result = self.client.send_message(
                    content=test_content,
                    uids=self.config['uids'] if self.config['uids'] else None,
                    topic_ids=self.config['topic_ids'] if self.config['topic_ids'] else None,
                    content_type=2,  # HTML格式
                    summary="WxPusher测试消息"
                )
                
                if result.get('code') == 1000:
                    logger.info("✅ WxPusher标准推送测试消息发送成功")
                else:
                    logger.error(f"❌ WxPusher标准推送测试失败: {result.get('msg')}")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ WxPusher标准推送测试异常: {e}")
                success = False
        
        # 极简推送测试
        if self.simple_client:
            try:
                simple_content = f"🧪 WxPusher测试消息\n📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n✅ 如果您收到此消息，说明WxPusher配置正确！"
                
                result = self.simple_client.send_message(
                    content=simple_content,
                    content_type=1,  # 文本格式
                    summary="WxPusher测试消息"
                )
                
                if result.get('code') == 1000:
                    logger.info("✅ WxPusher极简推送测试消息发送成功")
                else:
                    logger.error(f"❌ WxPusher极简推送测试失败: {result.get('msg')}")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ WxPusher极简推送测试异常: {e}")
                success = False
        
        return success
    
    def get_user_count(self) -> int:
        """获取关注用户数量"""
        if not self.client:
            return 0
        
        try:
            result = self.client.query_users(page=1, page_size=1)
            if result.get('code') == 1000:
                return result.get('data', {}).get('total', 0)
        except Exception as e:
            logger.error(f"查询用户数量失败: {e}")
        
        return 0
    
    def print_status(self):
        """打印WxPusher状态"""
        print(f"\n📱 WxPusher推送状态:")
        print(f"   启用状态: {'✅ 已启用' if self.is_enabled() else '❌ 已禁用'}")

        if self.is_enabled():
            if self.client:
                user_count = self.get_user_count()
                print(f"   标准推送: ✅ 已配置 (硬编码)")
                print(f"   APP_TOKEN: AT_fWXnH05M1MD8wFunlBRioiFtW5JL5yGm")
                print(f"   主题ID: 41366")
                print(f"   关注用户: {user_count} 人")
                print(f"   推送目标: {len(self.config['uids'])} 个UID, {len(self.config['topic_ids'])} 个主题")

            if self.simple_client:
                print(f"   极简推送: ✅ 已配置")


# 全局WxPusher发送器实例
wxpusher_sender = WxPusherSender()
