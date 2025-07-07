#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能推送系统 - 多渠道通知管理器
支持邮件、微信、钉钉、短信等多种推送方式
"""

import smtplib
import json
import time
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional
import os
from dataclasses import dataclass

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NotificationConfig:
    """通知配置类"""
    # 邮件配置
    email_enabled: bool = False
    smtp_server: str = "smtp.qq.com"
    smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_to: List[str] = None
    
    # 微信配置（Server酱）
    wechat_enabled: bool = False
    wechat_key: str = ""
    
    # 钉钉配置
    dingtalk_enabled: bool = False
    dingtalk_webhook: str = ""
    dingtalk_secret: str = ""
    
    # 短信配置（阿里云）
    sms_enabled: bool = False
    sms_access_key: str = ""
    sms_access_secret: str = ""
    sms_sign_name: str = ""
    sms_template_code: str = ""
    sms_phone_numbers: List[str] = None

class NotificationManager:
    """智能推送管理器"""
    
    def __init__(self, config_file: str = "notification_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self) -> NotificationConfig:
        """加载通知配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return NotificationConfig(**data)
            except Exception as e:
                logger.error(f"加载配置失败: {e}")
        
        # 返回默认配置
        return NotificationConfig()
    
    def save_config(self):
        """保存通知配置"""
        try:
            config_dict = {
                'email_enabled': self.config.email_enabled,
                'smtp_server': self.config.smtp_server,
                'smtp_port': self.config.smtp_port,
                'email_user': self.config.email_user,
                'email_password': self.config.email_password,
                'email_to': self.config.email_to or [],
                'wechat_enabled': self.config.wechat_enabled,
                'wechat_key': self.config.wechat_key,
                'dingtalk_enabled': self.config.dingtalk_enabled,
                'dingtalk_webhook': self.config.dingtalk_webhook,
                'dingtalk_secret': self.config.dingtalk_secret,
                'sms_enabled': self.config.sms_enabled,
                'sms_access_key': self.config.sms_access_key,
                'sms_access_secret': self.config.sms_access_secret,
                'sms_sign_name': self.config.sms_sign_name,
                'sms_template_code': self.config.sms_template_code,
                'sms_phone_numbers': self.config.sms_phone_numbers or []
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, ensure_ascii=False, indent=2)
            logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def setup_email(self, smtp_server: str, smtp_port: int, email_user: str, 
                   email_password: str, email_to: List[str]):
        """设置邮件通知"""
        self.config.email_enabled = True
        self.config.smtp_server = smtp_server
        self.config.smtp_port = smtp_port
        self.config.email_user = email_user
        self.config.email_password = email_password
        self.config.email_to = email_to
        self.save_config()
        logger.info("邮件通知已配置")
    
    def setup_wechat(self, wechat_key: str):
        """设置微信通知（Server酱）"""
        self.config.wechat_enabled = True
        self.config.wechat_key = wechat_key
        self.save_config()
        logger.info("微信通知已配置")
    
    def setup_dingtalk(self, webhook: str, secret: str = ""):
        """设置钉钉通知"""
        self.config.dingtalk_enabled = True
        self.config.dingtalk_webhook = webhook
        self.config.dingtalk_secret = secret
        self.save_config()
        logger.info("钉钉通知已配置")
    
    def send_email(self, subject: str, content: str, html_content: str = None, 
                   attachments: List[str] = None) -> bool:
        """发送邮件通知"""
        if not self.config.email_enabled or not self.config.email_to:
            logger.warning("邮件通知未启用或未配置收件人")
            return False
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config.email_user
            msg['To'] = ', '.join(self.config.email_to)
            msg['Subject'] = subject
            
            # 添加文本内容
            text_part = MIMEText(content, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # 添加HTML内容
            if html_content:
                html_part = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(html_part)
            
            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, 'rb') as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(file_path)}'
                        )
                        msg.attach(part)
            
            # 发送邮件
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.email_user, self.config.email_password)
            text = msg.as_string()
            server.sendmail(self.config.email_user, self.config.email_to, text)
            server.quit()
            
            logger.info(f"邮件发送成功: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def send_wechat(self, title: str, content: str) -> bool:
        """发送微信通知（Server酱）"""
        if not self.config.wechat_enabled or not self.config.wechat_key:
            logger.warning("微信通知未启用或未配置密钥")
            return False
        
        try:
            url = f"https://sctapi.ftqq.com/{self.config.wechat_key}.send"
            data = {
                'title': title,
                'desp': content
            }
            
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"微信通知发送成功: {title}")
                    return True
                else:
                    logger.error(f"微信通知发送失败: {result.get('message')}")
            else:
                logger.error(f"微信通知请求失败: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"微信通知发送异常: {e}")
            return False
    
    def send_dingtalk(self, title: str, content: str) -> bool:
        """发送钉钉通知"""
        if not self.config.dingtalk_enabled or not self.config.dingtalk_webhook:
            logger.warning("钉钉通知未启用或未配置Webhook")
            return False
        
        try:
            headers = {'Content-Type': 'application/json'}
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": f"# {title}\n\n{content}"
                }
            }
            
            # 如果有签名，添加时间戳和签名
            if self.config.dingtalk_secret:
                import hmac
                import hashlib
                import base64
                import urllib.parse
                
                timestamp = str(round(time.time() * 1000))
                secret_enc = self.config.dingtalk_secret.encode('utf-8')
                string_to_sign = f'{timestamp}\n{self.config.dingtalk_secret}'
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                
                url = f"{self.config.dingtalk_webhook}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.config.dingtalk_webhook
            
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info(f"钉钉通知发送成功: {title}")
                    return True
                else:
                    logger.error(f"钉钉通知发送失败: {result.get('errmsg')}")
            else:
                logger.error(f"钉钉通知请求失败: {response.status_code}")
            return False
            
        except Exception as e:
            logger.error(f"钉钉通知发送异常: {e}")
            return False
    
    def send_all(self, title: str, content: str, html_content: str = None) -> Dict[str, bool]:
        """发送所有启用的通知"""
        results = {}
        
        # 发送邮件
        if self.config.email_enabled:
            results['email'] = self.send_email(title, content, html_content)
        
        # 发送微信
        if self.config.wechat_enabled:
            results['wechat'] = self.send_wechat(title, content)
        
        # 发送钉钉
        if self.config.dingtalk_enabled:
            results['dingtalk'] = self.send_dingtalk(title, content)
        
        return results
    
    def generate_stock_report_html(self, stocks: List[Dict], title: str = "每日选股报告") -> str:
        """生成股票报告HTML"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{title}</title>
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header .time {{ font-size: 14px; opacity: 0.9; margin-top: 5px; }}
                .stock-card {{ background: white; margin: 10px 0; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .stock-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }}
                .stock-name {{ font-size: 18px; font-weight: bold; color: #333; }}
                .stock-code {{ color: #666; font-size: 14px; }}
                .stock-score {{ background: #4CAF50; color: white; padding: 5px 10px; border-radius: 15px; font-weight: bold; }}
                .stock-price {{ font-size: 16px; color: #E91E63; font-weight: bold; }}
                .stock-change {{ font-size: 14px; }}
                .change-positive {{ color: #4CAF50; }}
                .change-negative {{ color: #f44336; }}
                .stock-reasons {{ margin-top: 10px; }}
                .reason-tag {{ background: #e3f2fd; color: #1976d2; padding: 3px 8px; margin: 2px; border-radius: 12px; display: inline-block; font-size: 12px; }}
                .footer {{ text-align: center; margin-top: 20px; padding: 15px; background: #333; color: white; border-radius: 8px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 8px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🏆 {title}</h1>
                <div class="time">📅 报告时间: {current_time}</div>
            </div>
        """
        
        if stocks:
            html += f"<p style='font-size: 16px; color: #333;'>📊 今日发现 <strong>{len(stocks)}</strong> 只优质股票，详细分析如下：</p>"
            
            for i, stock in enumerate(stocks, 1):
                change_class = "change-positive" if stock.get('change_percent', 0) >= 0 else "change-negative"
                change_symbol = "+" if stock.get('change_percent', 0) >= 0 else ""
                
                html += f"""
                <div class="stock-card">
                    <div class="stock-header">
                        <div>
                            <span class="stock-name">#{i} {stock.get('name', 'N/A')}</span>
                            <span class="stock-code">({stock.get('code', 'N/A')})</span>
                        </div>
                        <span class="stock-score">{stock.get('score', 0)}分</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span class="stock-price">¥{stock.get('price', 0):.2f}</span>
                            <span class="stock-change {change_class}">
                                {change_symbol}{stock.get('change_percent', 0):.2f}%
                            </span>
                        </div>
                        <div style="text-align: right; font-size: 14px; color: #666;">
                            💰 市值: {stock.get('market_cap', 'N/A')}
                        </div>
                    </div>
                    <div class="stock-reasons">
                        <strong>🎯 推荐理由:</strong><br>
                """
                
                reasons = stock.get('reasons', '').split(' | ')
                for reason in reasons:
                    if reason.strip():
                        html += f'<span class="reason-tag">{reason.strip()}</span>'
                
                html += """
                    </div>
                </div>
                """
        else:
            html += """
            <div style="text-align: center; padding: 40px; background: white; border-radius: 8px;">
                <h3 style="color: #666;">📉 今日未发现符合条件的股票</h3>
                <p style="color: #999;">建议调整筛选参数或关注市场变化</p>
            </div>
            """
        
        html += """
            <div class="warning">
                <strong>⚠️ 重要提醒:</strong><br>
                • 本分析基于技术指标和量化模型，仅供参考<br>
                • 股市有风险，投资需谨慎<br>
                • 建议结合基本面分析和市场环境做最终决策<br>
                • 请根据个人风险承受能力合理配置仓位
            </div>
            
            <div class="footer">
                <p>🤖 智能选股系统 v2.0 | 📊 基于AkShare实时数据</p>
                <p style="font-size: 12px; opacity: 0.8;">本系统由AI驱动，持续优化中...</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def send_daily_report(self, stocks: List[Dict], title: str = "每日选股报告"):
        """发送每日选股报告"""
        # 生成纯文本内容
        text_content = f"{title}\n{'='*50}\n"
        text_content += f"📅 报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if stocks:
            text_content += f"📊 今日发现 {len(stocks)} 只优质股票：\n\n"
            for i, stock in enumerate(stocks, 1):
                change_symbol = "+" if stock.get('change_percent', 0) >= 0 else ""
                text_content += f"#{i} {stock.get('name', 'N/A')} ({stock.get('code', 'N/A')})\n"
                text_content += f"   💰 价格: ¥{stock.get('price', 0):.2f} ({change_symbol}{stock.get('change_percent', 0):.2f}%)\n"
                text_content += f"   📊 评分: {stock.get('score', 0)}分\n"
                text_content += f"   🎯 理由: {stock.get('reasons', 'N/A')}\n\n"
        else:
            text_content += "📉 今日未发现符合条件的股票\n"
        
        text_content += "\n⚠️ 重要提醒: 股市有风险，投资需谨慎！\n"
        text_content += "🤖 智能选股系统 v2.0"
        
        # 生成HTML内容
        html_content = self.generate_stock_report_html(stocks, title)
        
        # 发送通知
        results = self.send_all(title, text_content, html_content)
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        logger.info(f"每日报告发送完成: {success_count}/{total_count} 个渠道成功")
        return results

def main():
    """配置向导"""
    print("🔔 智能推送系统配置向导")
    print("="*50)
    
    manager = NotificationManager()
    
    while True:
        print("\n请选择要配置的通知方式:")
        print("1. 📧 邮件通知")
        print("2. 📱 微信通知 (Server酱)")
        print("3. 💬 钉钉通知")
        print("4. 📋 查看当前配置")
        print("5. 🧪 发送测试通知")
        print("0. 退出")
        
        choice = input("\n请输入选择 (0-5): ").strip()
        
        if choice == "1":
            print("\n📧 配置邮件通知")
            smtp_server = input("SMTP服务器 (默认: smtp.qq.com): ").strip() or "smtp.qq.com"
            smtp_port = int(input("SMTP端口 (默认: 587): ").strip() or "587")
            email_user = input("发送邮箱: ").strip()
            email_password = input("邮箱密码/授权码: ").strip()
            email_to = input("接收邮箱 (多个用逗号分隔): ").strip().split(',')
            email_to = [email.strip() for email in email_to if email.strip()]
            
            manager.setup_email(smtp_server, smtp_port, email_user, email_password, email_to)
            print("✅ 邮件通知配置成功!")
            
        elif choice == "2":
            print("\n📱 配置微信通知")
            print("请先到 https://sct.ftqq.com/ 获取SendKey")
            wechat_key = input("请输入Server酱SendKey: ").strip()
            
            manager.setup_wechat(wechat_key)
            print("✅ 微信通知配置成功!")
            
        elif choice == "3":
            print("\n💬 配置钉钉通知")
            print("请先在钉钉群中添加自定义机器人获取Webhook")
            webhook = input("钉钉Webhook地址: ").strip()
            secret = input("钉钉机器人密钥 (可选): ").strip()
            
            manager.setup_dingtalk(webhook, secret)
            print("✅ 钉钉通知配置成功!")
            
        elif choice == "4":
            print("\n📋 当前配置状态:")
            print(f"📧 邮件通知: {'✅ 已启用' if manager.config.email_enabled else '❌ 未启用'}")
            print(f"📱 微信通知: {'✅ 已启用' if manager.config.wechat_enabled else '❌ 未启用'}")
            print(f"💬 钉钉通知: {'✅ 已启用' if manager.config.dingtalk_enabled else '❌ 未启用'}")
            
        elif choice == "5":
            print("\n🧪 发送测试通知...")
            test_stocks = [
                {
                    'name': '测试股票',
                    'code': '000001',
                    'price': 10.50,
                    'change_percent': 2.5,
                    'score': 85,
                    'market_cap': '100亿',
                    'reasons': '技术指标良好 | 成交量放大 | 多头排列'
                }
            ]
            
            results = manager.send_daily_report(test_stocks, "📊 选股系统测试报告")
            
            for channel, success in results.items():
                status = "✅ 成功" if success else "❌ 失败"
                print(f"{channel}: {status}")
                
        elif choice == "0":
            print("👋 配置完成，感谢使用!")
            break
        else:
            print("❌ 无效选择，请重新输入")

if __name__ == "__main__":
    main() 