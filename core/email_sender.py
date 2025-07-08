#!/usr/bin/env python3
"""
邮件发送模块
用于发送选股结果到指定邮箱
"""

import smtplib
import json
import os
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Optional

class EmailSender:
    """邮件发送器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.enabled = config.get('enabled', False)
        
    def send_selection_results(self, strategy_name: str, results_file: str, 
                             to_email: Optional[str] = None) -> bool:
        """
        发送选股结果邮件
        
        Args:
            strategy_name: 策略名称 (technical/comprehensive)
            results_file: 结果文件路径
            to_email: 接收邮箱，如果为None则使用配置中的默认邮箱
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            print("邮件通知已禁用")
            return False
            
        try:
            # 读取结果文件
            if not os.path.exists(results_file):
                print(f"结果文件不存在: {results_file}")
                return False
                
            with open(results_file, 'r', encoding='utf-8') as f:
                results = json.load(f)
            
            # 生成邮件内容
            subject = self.config.get('subject_template', '📈 每日选股推荐 - {date}').format(
                date=datetime.now().strftime('%Y-%m-%d')
            )
            
            # 生成HTML内容
            html_content = self._generate_html_content(strategy_name, results)
            
            # 发送邮件
            return self._send_email(
                to_email or self.config.get('to_email'),
                subject,
                html_content,
                results_file
            )
            
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False
    
    def _generate_html_content(self, strategy_name: str, results: List[Dict]) -> str:
        """生成HTML邮件内容"""
        
        strategy_display_names = {
            'technical': '技术分析策略',
            'comprehensive': '四维综合分析策略'
        }
        
        display_name = strategy_display_names.get(strategy_name, strategy_name)
        
        # 生成股票表格HTML
        stocks_html = ""
        for i, stock in enumerate(results, 1):
            reasons = ' | '.join(stock.get('reasons', ['综合评分优秀']))
            price = stock.get('price', 0)
            market_cap = stock.get('market_cap', 0)
            
            stocks_html += f"""
            <tr>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: center;">{i}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{stock['code']}</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{stock['name']}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: center; color: #e74c3c; font-weight: bold;">{stock['score']}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{price:.2f}</td>
                <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{market_cap:.1f}亿</td>
                <td style="border: 1px solid #ddd; padding: 8px;">{reasons}</td>
            </tr>
            """
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>每日选股推荐</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; }}
                .content {{ margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th {{ background-color: #f8f9fa; border: 1px solid #ddd; padding: 12px; text-align: center; font-weight: bold; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 20px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📈 每日选股推荐</h1>
                <p>策略: {display_name} | 日期: {datetime.now().strftime('%Y年%m月%d日')}</p>
            </div>
            
            <div class="content">
                <h2>🎯 今日推荐股票 ({len(results)}只)</h2>
                
                <table>
                    <thead>
                        <tr>
                            <th>序号</th>
                            <th>代码</th>
                            <th>名称</th>
                            <th>得分</th>
                            <th>价格</th>
                            <th>市值</th>
                            <th>推荐理由</th>
                        </tr>
                    </thead>
                    <tbody>
                        {stocks_html}
                    </tbody>
                </table>
            </div>
            
            <div class="warning">
                <strong>⚠️ 风险提示:</strong> 本结果仅为量化分析，不构成投资建议。投资有风险，入市需谨慎。
            </div>
            
            <div class="footer">
                <p>📧 本邮件由 A股智能选股系统 自动生成</p>
                <p>🕐 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
        </html>
        """
        
        return html_template
    
    def _send_email(self, to_email: str, subject: str, html_content: str, 
                   attachment_path: Optional[str] = None) -> bool:
        """发送邮件"""
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['username']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 添加附件（结果文件）
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, 'rb') as f:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {os.path.basename(attachment_path)}'
                    )
                    msg.attach(part)
            
            # 根据端口选择连接方式
            port = self.config.get('smtp_port', 587)
            use_tls = self.config.get('use_tls', True)
            
            if port == 465:
                # 使用SSL连接
                server = smtplib.SMTP_SSL(self.config['smtp_server'], port)
            else:
                # 使用TLS连接
                server = smtplib.SMTP(self.config['smtp_server'], port)
                if use_tls:
                    server.starttls()
            
            server.login(self.config['username'], self.config['password'])
            server.send_message(msg)
            server.quit()
            
            print(f"✅ 邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False

def send_notification_email(strategy_name: str, results_file: str, 
                          config: Dict, to_email: Optional[str] = None) -> bool:
    """
    发送通知邮件的便捷函数
    
    Args:
        strategy_name: 策略名称
        results_file: 结果文件路径
        config: 邮件配置
        to_email: 接收邮箱（可选）
    
    Returns:
        bool: 发送是否成功
    """
    sender = EmailSender(config)
    return sender.send_selection_results(strategy_name, results_file, to_email) 