#!/usr/bin/env python3
"""
个人A股选股系统 - 主程序入口
支持定时任务和命令行操作
"""

import sys
import schedule
import time
import logging
import argparse
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import Config, init_config
from stock_selector import PersonalStockSelector

# 配置日志
def setup_logging():
    """设置日志配置"""
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, Config.LOGGING_CONFIG['level']))
    
    formatter = logging.Formatter(Config.LOGGING_CONFIG['format'])
    
    # 控制台处理器
    if Config.LOGGING_CONFIG['console_handler']['enabled']:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 文件处理器
    if Config.LOGGING_CONFIG['file_handler']['enabled']:
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            Config.LOGGING_CONFIG['file_handler']['filename'],
            maxBytes=Config.LOGGING_CONFIG['file_handler']['max_bytes'],
            backupCount=Config.LOGGING_CONFIG['file_handler']['backup_count'],
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

class StockSelectorApp:
    """选股应用主类"""
    
    def __init__(self):
        self.selector = PersonalStockSelector(Config.STOCK_FILTER)
        self.logger = logging.getLogger(__name__)
    
    def send_email_notification(self, stocks):
        """发送邮件通知"""
        if not Config.EMAIL_CONFIG['enabled']:
            return
        
        try:
            # 创建邮件内容
            subject = Config.EMAIL_CONFIG['subject_template'].format(
                date=datetime.now().strftime('%Y-%m-%d')
            )
            
            # 生成HTML邮件内容
            html_content = self.generate_email_html(stocks)
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = Config.EMAIL_CONFIG['username']
            msg['To'] = Config.EMAIL_CONFIG['to_email']
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 发送邮件
            server = smtplib.SMTP(Config.EMAIL_CONFIG['smtp_server'], Config.EMAIL_CONFIG['smtp_port'])
            if Config.EMAIL_CONFIG['use_tls']:
                server.starttls()
            server.login(Config.EMAIL_CONFIG['username'], Config.EMAIL_CONFIG['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"邮件通知发送成功: {Config.EMAIL_CONFIG['to_email']}")
            
        except Exception as e:
            self.logger.error(f"发送邮件失败: {e}")
    
    def generate_email_html(self, stocks):
        """生成邮件HTML内容"""
        if not stocks:
            return """
            <html>
            <body>
                <h2>📈 今日选股推荐</h2>
                <p>今日暂无符合条件的推荐股票</p>
                <p style="color: #666; font-size: 12px;">
                    本推荐仅基于技术分析，不构成投资建议。股市有风险，投资需谨慎。
                </p>
            </body>
            </html>
            """
        
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                .stock-item { 
                    background-color: #f8f9fa; 
                    margin: 10px 0; 
                    padding: 15px; 
                    border-radius: 5px;
                    border-left: 4px solid #3498db;
                }
                .stock-name { font-size: 18px; font-weight: bold; color: #2c3e50; }
                .stock-details { margin: 5px 0; color: #34495e; }
                .score { color: #e74c3c; font-weight: bold; }
                .reasons { color: #27ae60; }
                .warning { 
                    background-color: #fff3cd; 
                    border: 1px solid #ffeaa7; 
                    padding: 10px; 
                    margin: 20px 0;
                    border-radius: 5px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h2>📈 今日选股推荐 - {date}</h2>
            </div>
        """.format(date=datetime.now().strftime('%Y-%m-%d'))
        
        for i, stock in enumerate(stocks, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
            
            html += f"""
            <div class="stock-item">
                <div class="stock-name">{medal} {stock['name']} ({stock['code']})</div>
                <div class="stock-details">评分: <span class="score">{stock['score']}/100</span></div>
                <div class="stock-details">当前价格: ¥{stock['current_price']}</div>
                <div class="stock-details">市值: {stock['market_cap']/100000000:.0f}亿</div>
                <div class="stock-details">近30日涨幅: {stock['recent_gain']:+.1f}%</div>
            """
            
            if stock['reasons']:
                html += f'<div class="stock-details">推荐理由: <span class="reasons">{" + ".join(stock["reasons"])}</span></div>'
            
            html += '</div>'
        
        html += """
            <div class="warning">
                <strong>⚠️ 风险提示:</strong><br>
                本推荐仅基于技术分析，不构成投资建议。<br>
                股市有风险，投资需谨慎，请结合基本面分析和个人风险承受能力。
            </div>
        </body>
        </html>
        """
        
        return html
    
    def run_daily_selection(self):
        """执行每日选股"""
        self.logger.info("开始执行每日选股任务")
        
        try:
            # 执行选股
            results = self.selector.daily_stock_selection()
            
            # 发送通知
            if results:
                self.send_email_notification(results)
                self.logger.info(f"选股完成，推荐 {len(results)} 只股票")
            else:
                self.logger.info("今日无推荐股票")
                self.send_email_notification([])  # 发送空结果通知
                
        except Exception as e:
            self.logger.error(f"选股任务执行失败: {e}")
    
    def start_scheduler(self):
        """启动定时任务"""
        if not Config.SCHEDULE_CONFIG['enabled']:
            self.logger.info("定时任务已禁用")
            return
        
        run_time = Config.SCHEDULE_CONFIG['run_time']
        self.logger.info(f"设置定时任务: 每日 {run_time} 执行选股")
        
        if Config.SCHEDULE_CONFIG['weekdays_only']:
            # 仅工作日执行
            schedule.every().monday.at(run_time.strftime('%H:%M')).do(self.run_daily_selection)
            schedule.every().tuesday.at(run_time.strftime('%H:%M')).do(self.run_daily_selection)
            schedule.every().wednesday.at(run_time.strftime('%H:%M')).do(self.run_daily_selection)
            schedule.every().thursday.at(run_time.strftime('%H:%M')).do(self.run_daily_selection)
            schedule.every().friday.at(run_time.strftime('%H:%M')).do(self.run_daily_selection)
            self.logger.info("定时任务设置为仅工作日执行")
        else:
            # 每日执行
            schedule.every().day.at(run_time.strftime('%H:%M')).do(self.run_daily_selection)
            self.logger.info("定时任务设置为每日执行")
        
        self.logger.info("定时任务已启动，等待执行...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            self.logger.info("定时任务已停止")

def create_argument_parser():
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description='个人A股选股系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py run                    # 立即执行一次选股
  python main.py schedule               # 启动定时任务
  python main.py test                   # 运行测试模式
  python main.py history --days 7      # 查看近7天历史结果
  python main.py config                 # 初始化配置
        """
    )
    
    parser.add_argument('command', choices=['run', 'schedule', 'test', 'history', 'config'],
                       help='执行的命令')
    parser.add_argument('--days', type=int, default=7,
                       help='历史查询天数 (默认: 7)')
    parser.add_argument('--debug', action='store_true',
                       help='启用调试模式')
    
    return parser

def main():
    """主函数"""
    # 解析命令行参数
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # 初始化配置
    init_config()
    
    # 设置日志
    if args.debug:
        Config.LOGGING_CONFIG['level'] = 'DEBUG'
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info(f"启动 {Config.APP_NAME} v{Config.VERSION}")
    
    # 创建应用实例
    app = StockSelectorApp()
    
    # 执行对应命令
    if args.command == 'run':
        logger.info("执行立即选股")
        app.run_daily_selection()
        
    elif args.command == 'schedule':
        logger.info("启动定时任务模式")
        app.start_scheduler()
        
    elif args.command == 'test':
        logger.info("执行测试模式")
        from stock_selector import quick_test
        quick_test()
        
    elif args.command == 'history':
        logger.info(f"查看近{args.days}天历史结果")
        app.selector.analyze_performance(args.days)
        
    elif args.command == 'config':
        logger.info("初始化配置")
        print("配置已初始化完成")
        print("请查看 user_config_template.py 并复制为 user_config.py 进行个性化配置")

if __name__ == "__main__":
    main() 