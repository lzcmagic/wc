#!/usr/bin/env python3
"""
WxPusher微信推送客户端
用于A股选股系统的消息推送功能
"""

import requests
import json
from typing import List, Dict, Optional, Union
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class WxPusherClient:
    """WxPusher微信推送客户端"""
    
    def __init__(self, app_token: str):
        """
        初始化WxPusher客户端
        
        Args:
            app_token: WxPusher应用的APP_TOKEN
        """
        self.app_token = app_token
        self.base_url = "https://wxpusher.zjiecode.com/api"
        
    def send_message(self, 
                    content: str,
                    uids: Optional[List[str]] = None,
                    topic_ids: Optional[List[int]] = None,
                    content_type: int = 2,  # 2=HTML, 1=文本, 3=markdown
                    summary: Optional[str] = None,
                    url: Optional[str] = None,
                    verify_pay_type: int = 0) -> Dict:
        """
        发送消息
        
        Args:
            content: 消息内容
            uids: 用户UID列表
            topic_ids: 主题ID列表
            content_type: 内容类型 1=文本 2=HTML 3=markdown
            summary: 消息摘要(最多20字符)
            url: 原文链接
            verify_pay_type: 付费验证 0=不验证 1=只发付费用户 2=只发免费用户
            
        Returns:
            发送结果
        """
        if not uids and not topic_ids:
            raise ValueError("uids和topic_ids至少需要提供一个")
            
        # 构建请求数据
        data = {
            "appToken": self.app_token,
            "content": content,
            "contentType": content_type,
            "verifyPayType": verify_pay_type
        }
        
        if uids:
            data["uids"] = uids
        if topic_ids:
            data["topicIds"] = topic_ids
        if summary:
            data["summary"] = summary[:20]  # 限制20字符
        if url:
            data["url"] = url
            
        try:
            response = requests.post(
                f"{self.base_url}/send/message",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if result.get("code") == 1000:
                logger.info(f"消息发送成功，发送给 {len(uids or [])} 个用户")
                return result
            else:
                logger.error(f"消息发送失败: {result.get('msg')}")
                return result
                
        except Exception as e:
            logger.error(f"发送消息时出错: {e}")
            return {"code": -1, "msg": str(e), "success": False}
    
    def send_stock_selection_result(self, 
                                  stocks: List[Dict],
                                  strategy_name: str,
                                  uids: Optional[List[str]] = None,
                                  topic_ids: Optional[List[int]] = None,
                                  date: Optional[str] = None) -> Dict:
        """
        发送选股结果
        
        Args:
            stocks: 选股结果列表
            strategy_name: 策略名称
            uids: 用户UID列表
            topic_ids: 主题ID列表
            date: 选股日期
            
        Returns:
            发送结果
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        # 构建HTML消息内容
        html_content = self._build_stock_html(stocks, strategy_name, date)
        
        # 构建消息摘要
        summary = f"{strategy_name}选股({len(stocks)}只)"
        
        return self.send_message(
            content=html_content,
            uids=uids,
            topic_ids=topic_ids,
            content_type=2,  # HTML格式
            summary=summary
        )
    
    def _build_stock_html(self, stocks: List[Dict], strategy_name: str, date: str) -> str:
        """构建选股结果的HTML内容"""
        
        html = f"""
        <h2>🎯 {strategy_name}策略选股结果</h2>
        <p><strong>📅 日期:</strong> {date}</p>
        <p><strong>📊 选中股票:</strong> {len(stocks)} 只</p>
        <hr/>
        """
        
        if not stocks:
            html += "<p style='color: #999;'>今日暂无符合条件的股票</p>"
        else:
            html += "<div>"
            for i, stock in enumerate(stocks[:10], 1):  # 限制显示前10只
                code = stock.get('code', 'N/A')
                name = stock.get('name', 'N/A')
                score = stock.get('score', 0)
                # 兼容两种字段名：price 和 current_price
                current_price = stock.get('price', stock.get('current_price', 0))
                change_pct = stock.get('change_pct', 0)
                
                # 涨跌颜色
                color = "#ff4444" if change_pct < 0 else "#00aa00" if change_pct > 0 else "#666"
                change_text = f"{change_pct:+.2f}%" if change_pct != 0 else "0.00%"
                
                html += f"""
                <div style='border: 1px solid #ddd; margin: 8px 0; padding: 10px; border-radius: 5px;'>
                    <div style='font-weight: bold; font-size: 16px;'>
                        {i}. {name} ({code})
                    </div>
                    <div style='margin-top: 5px;'>
                        <span>💰 {current_price:.2f}元</span>
                        <span style='color: {color}; margin-left: 10px;'>{change_text}</span>
                        <span style='margin-left: 10px;'>⭐ {score:.1f}分</span>
                    </div>
                </div>
                """
            
            if len(stocks) > 10:
                html += f"<p style='color: #666; text-align: center;'>... 还有 {len(stocks) - 10} 只股票</p>"
                
            html += "</div>"
        
        html += f"""
        <hr/>
        <p style='color: #999; font-size: 12px;'>
            ⚠️ 本信息仅供参考，不构成投资建议<br/>
            🤖 由A股智能选股系统自动生成
        </p>
        """
        
        return html
    
    def query_users(self, page: int = 1, page_size: int = 50, uid: Optional[str] = None) -> Dict:
        """
        查询关注用户列表
        
        Args:
            page: 页码
            page_size: 页面大小
            uid: 特定用户UID
            
        Returns:
            用户列表
        """
        params = {
            "appToken": self.app_token,
            "page": page,
            "pageSize": min(page_size, 100)  # 最大100
        }
        
        if uid:
            params["uid"] = uid
            
        try:
            response = requests.get(
                f"{self.base_url}/fun/wxuser/v2",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"查询用户列表时出错: {e}")
            return {"code": -1, "msg": str(e), "success": False}
    
    def create_qrcode(self, extra: str, valid_time: int = 1800) -> Dict:
        """
        创建参数二维码
        
        Args:
            extra: 二维码携带的参数
            valid_time: 有效期(秒)，默认30分钟
            
        Returns:
            二维码信息
        """
        data = {
            "appToken": self.app_token,
            "extra": extra,
            "validTime": valid_time
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/fun/create/qrcode",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"创建二维码时出错: {e}")
            return {"code": -1, "msg": str(e), "success": False}


class WxPusherSimpleClient:
    """WxPusher极简推送客户端"""
    
    def __init__(self, spt: str):
        """
        初始化极简推送客户端
        
        Args:
            spt: Simple Push Token
        """
        self.spt = spt
        self.base_url = "https://wxpusher.zjiecode.com/api"
    
    def send_message(self, content: str, content_type: int = 2, summary: Optional[str] = None, url: Optional[str] = None) -> Dict:
        """
        发送消息（极简模式）
        
        Args:
            content: 消息内容
            content_type: 内容类型
            summary: 消息摘要
            url: 原文链接
            
        Returns:
            发送结果
        """
        data = {
            "content": content,
            "contentType": content_type,
            "spt": self.spt
        }
        
        if summary:
            data["summary"] = summary[:20]
        if url:
            data["url"] = url
            
        try:
            response = requests.post(
                f"{self.base_url}/send/message/simple-push",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"极简推送发送消息时出错: {e}")
            return {"code": -1, "msg": str(e), "success": False}
