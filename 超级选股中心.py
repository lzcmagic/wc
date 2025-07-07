#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 超级智能选股中心 - 一站式投资决策平台
集成所有功能模块的统一控制面板
"""

import os
import sys
import time
import subprocess
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SuperStockCenter:
    """超级选股中心主控制器"""
    
    def __init__(self):
        self.version = "v2.0"
        self.modules = {
            "1": {"name": "🔍 全市场智能扫描", "file": "full_market_scanner.py", "desc": "扫描全市场5000+股票，智能选出优质标的"},
            "2": {"name": "📊 专业技术分析", "file": "market_analyzer.py", "desc": "20+技术指标深度分析，四维评分系统"},
            "3": {"name": "🔔 智能推送通知", "file": "notification_manager.py", "desc": "邮件/微信/钉钉多渠道推送，HTML精美报告"},
            "4": {"name": "📱 移动端Web应用", "file": "mobile_web_app.py", "desc": "响应式设计，PWA支持，随时随地选股"},
            "5": {"name": "🤖 自动化调度", "file": "scheduler_manager.py", "desc": "定时任务，智能监控，故障恢复"},
            "6": {"name": "🔄 行业轮动分析", "file": "sector_rotation.py", "desc": "热点追踪，板块轮动预测，资金流向分析"},
            "7": {"name": "⚠️ 风险管理系统", "file": "risk_management.py", "desc": "止损预警，仓位管理，VaR计算"},
            "8": {"name": "📈 业绩跟踪分析", "file": "performance_tracker.py", "desc": "收益分析，策略回测，基准对比"},
            "9": {"name": "⚙️ 系统配置管理", "file": "config.py", "desc": "个性化配置，参数调优"},
            "10": {"name": "📊 摸鱼专用版", "file": "摸鱼选股.py", "desc": "上班摸鱼专用，隐蔽性强"}
        }
        
        self.quick_actions = {
            "A": {"name": "⚡ 快速选股", "action": self.quick_scan},
            "B": {"name": "📊 今日推荐", "action": self.daily_recommend},
            "C": {"name": "🔔 发送通知", "action": self.send_notification},
            "D": {"name": "📱 启动Web", "action": self.start_web},
            "E": {"name": "🎯 风险检查", "action": self.risk_check}
        }
    
    def show_banner(self):
        """显示欢迎横幅"""
        banner = f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    🚀 超级智能选股中心 {self.version}                              ║
║    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━              ║
║                                                              ║
║    🎯 AI驱动的A股投资决策平台                                    ║
║    📊 7大核心功能 | 🔍 全市场扫描 | 📱 移动端支持                  ║
║    🤖 自动化调度 | ⚠️ 风险管控 | 📈 业绩追踪                      ║
║                                                              ║
║    ⚡ 当前状态: 所有系统就绪                                       ║
║    📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                    ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(banner)
    
    def show_system_status(self):
        """显示系统状态"""
        print("🔍 系统状态检查:")
        
        # 检查文件存在性
        missing_files = []
        for module_id, module_info in self.modules.items():
            if not os.path.exists(module_info["file"]):
                missing_files.append(module_info["file"])
        
        if missing_files:
            print(f"   ❌ 缺失文件: {', '.join(missing_files)}")
        else:
            print("   ✅ 所有模块文件完整")
        
        # 检查日志目录
        if not os.path.exists('logs'):
            os.makedirs('logs')
            print("   📁 创建日志目录")
        else:
            print("   ✅ 日志目录存在")
        
        # 检查数据目录
        for directory in ['results', 'enhanced_results', 'sector_data', 'cache']:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"   📁 创建{directory}目录")
            else:
                print(f"   ✅ {directory}目录存在")
        
        print("   🎉 系统状态良好\n")
    
    def show_main_menu(self):
        """显示主菜单"""
        print("🎛️ 功能模块:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        for module_id, module_info in self.modules.items():
            print(f"   {module_id:>2}. {module_info['name']}")
            print(f"       💡 {module_info['desc']}")
        
        print("\n⚡ 快捷操作:")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        for action_id, action_info in self.quick_actions.items():
            print(f"   {action_id}. {action_info['name']}")
        
        print("\n   0. 退出系统")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    def run_module(self, module_file: str, desc: str = ""):
        """运行指定模块"""
        if not os.path.exists(module_file):
            print(f"❌ 文件不存在: {module_file}")
            return
        
        print(f"🚀 启动模块: {desc}")
        print(f"📂 执行文件: {module_file}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        try:
            # 使用subprocess运行模块
            process = subprocess.Popen([sys.executable, module_file], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE, 
                                     text=True)
            
            # 实时显示输出
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # 获取剩余输出
            stdout, stderr = process.communicate()
            if stdout:
                print(stdout)
            if stderr:
                print(f"错误信息: {stderr}")
            
            return_code = process.returncode
            if return_code == 0:
                print("✅ 模块执行完成")
            else:
                print(f"❌ 模块执行失败，返回码: {return_code}")
                
        except KeyboardInterrupt:
            print("\n⏹️ 用户中断执行")
        except Exception as e:
            print(f"❌ 执行错误: {e}")
        
        input("\n按回车键返回主菜单...")
    
    def quick_scan(self):
        """快速选股"""
        print("⚡ 执行快速选股...")
        
        # 执行全市场扫描
        try:
            from full_market_scanner import FullMarketScanner
            scanner = FullMarketScanner()
            results = scanner.scan_full_market(min_score=65, max_results=10, sample_size=200)
            
            if results:
                print(f"\n🎉 快速扫描完成，发现 {len(results)} 只优质股票:")
                for i, stock in enumerate(results[:5], 1):
                    print(f"   {i}. {stock['name']} ({stock['code']}) - {stock['score']}分")
            else:
                print("❌ 未发现符合条件的股票")
                
        except Exception as e:
            print(f"❌ 快速选股失败: {e}")
        
        input("\n按回车键继续...")
    
    def daily_recommend(self):
        """今日推荐"""
        print("📊 生成今日推荐...")
        
        try:
            # 执行市场分析
            from market_analyzer import MarketAnalyzer
            analyzer = MarketAnalyzer()
            
            print("🔍 正在分析核心股票...")
            core_stocks = ['000001', '000002', '600000', '600036', '000858']
            
            for code in core_stocks:
                result = analyzer.analyze_single_stock(code)
                if result:
                    print(f"   📈 {result.get('name', code)}: {result.get('signal', 'N/A')}")
            
        except Exception as e:
            print(f"❌ 生成推荐失败: {e}")
        
        input("\n按回车键继续...")
    
    def send_notification(self):
        """发送通知"""
        print("🔔 发送测试通知...")
        
        try:
            from notification_manager import NotificationManager
            nm = NotificationManager()
            
            test_stocks = [{
                'name': '测试推荐',
                'code': '000001',
                'price': 10.50,
                'change_percent': 2.5,
                'score': 85,
                'market_cap': '100亿',
                'reasons': '技术指标优秀 | 成交量放大 | 多头排列'
            }]
            
            results = nm.send_daily_report(test_stocks, "🚀 超级选股中心测试通知")
            
            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)
            
            print(f"📤 通知发送完成: {success_count}/{total_count} 个渠道成功")
            
        except Exception as e:
            print(f"❌ 发送通知失败: {e}")
        
        input("\n按回车键继续...")
    
    def start_web(self):
        """启动Web应用"""
        print("📱 启动移动端Web应用...")
        print("🌐 应用将在 http://localhost:5000 启动")
        print("💡 使用 Ctrl+C 停止服务")
        
        try:
            self.run_module("mobile_web_app.py", "移动端Web应用")
        except Exception as e:
            print(f"❌ 启动Web应用失败: {e}")
    
    def risk_check(self):
        """风险检查"""
        print("🎯 执行风险检查...")
        
        try:
            from risk_management import RiskManager
            risk_manager = RiskManager()
            
            # 构建投资组合
            positions = risk_manager.build_portfolio()
            
            if not positions:
                print("ℹ️ 暂无持仓数据，无法进行风险检查")
                print("💡 请先在风险管理系统中添加持仓")
            else:
                # 计算风险指标
                metrics = risk_manager.calculate_portfolio_metrics(positions)
                alerts = risk_manager.check_risk_alerts(positions, metrics)
                
                print(f"📊 组合总值: ¥{metrics.portfolio_value:,.2f}")
                print(f"📉 最大回撤: {metrics.max_drawdown:.1%}")
                print(f"⚡ 波动率: {metrics.volatility:.1%}")
                
                if alerts:
                    print(f"\n🚨 发现 {len(alerts)} 个风险预警")
                else:
                    print("\n✅ 当前无风险预警")
                
        except Exception as e:
            print(f"❌ 风险检查失败: {e}")
        
        input("\n按回车键继续...")
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
📚 系统使用帮助
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 系统概述:
   本系统是一个完整的A股智能选股平台，集成了市场扫描、技术分析、
   风险管理、业绩跟踪等多个专业模块。

⚡ 快速上手:
   1. 首次使用建议先执行"快速选股"(A键)
   2. 配置通知推送功能(模块3)
   3. 设置风险管理参数(模块7)
   4. 启用自动化调度(模块5)

🔍 核心功能:
   • 全市场扫描: 从5000+股票中智能筛选
   • 技术分析: 20+专业指标深度分析
   • 风险管控: 实时监控投资组合风险
   • 自动化: 定时执行、智能推送

📱 移动端:
   启动Web应用后，可在手机浏览器中访问 http://你的IP:5000
   支持PWA安装，获得原生应用体验

⚠️ 重要提醒:
   • 本系统仅供投资参考，不构成投资建议
   • 股市有风险，投资需谨慎
   • 建议结合基本面分析做最终决策

📞 技术支持:
   如遇问题，请检查logs目录下的日志文件
"""
        print(help_text)
        input("\n按回车键继续...")
    
    def run(self):
        """运行主程序"""
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')  # 清屏
                
                self.show_banner()
                self.show_system_status()
                self.show_main_menu()
                
                choice = input("\n🎯 请选择功能 (输入数字或字母): ").strip().upper()
                
                if choice == "0":
                    print("\n👋 感谢使用超级智能选股中心!")
                    print("🎉 祝您投资顺利，收益满满!")
                    break
                
                elif choice in self.modules:
                    module_info = self.modules[choice]
                    self.run_module(module_info["file"], module_info["name"])
                
                elif choice in self.quick_actions:
                    action_info = self.quick_actions[choice]
                    print(f"\n⚡ 执行快捷操作: {action_info['name']}")
                    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
                    action_info["action"]()
                
                elif choice == "H" or choice == "HELP":
                    self.show_help()
                
                else:
                    print(f"❌ 无效选择: {choice}")
                    print("💡 提示: 输入 H 查看帮助")
                    input("\n按回车键继续...")
        
        except KeyboardInterrupt:
            print("\n\n⏹️ 用户中断，正在退出...")
            print("👋 再见!")
        
        except Exception as e:
            print(f"\n❌ 系统错误: {e}")
            logger.error(f"系统错误: {e}")

def main():
    """主入口"""
    center = SuperStockCenter()
    center.run()

if __name__ == "__main__":
    main() 