#!/usr/bin/env python3
"""
GitHub Actions 环境测试脚本
模拟 GitHub Actions 的运行环境，验证选股策略是否能正常工作
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def test_environment():
    """测试环境配置"""
    print("🔍 测试环境配置...")
    
    # 检查 Python 版本
    python_version = sys.version_info
    print(f"   Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的包
    required_packages = [
        'akshare', 'pandas', 'numpy', 'flask', 'requests', 
        'python-dateutil', 'matplotlib', 'plotly', 'pandas-ta'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 缺少包: {', '.join(missing_packages)}")
        return False
    
    print("✅ 环境配置正常")
    return True

def test_imports():
    """测试关键模块导入"""
    print("\n🔍 测试模块导入...")
    
    try:
        from core.config import Config
        from strategies.technical_strategy import TechnicalStrategySelector
        from strategies.comprehensive_strategy import ComprehensiveStrategySelector
        from data_fetcher import StockDataFetcher
        print("✅ 所有模块导入成功")
        return True
    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False

def test_data_fetcher():
    """测试数据获取功能"""
    print("\n🔍 测试数据获取...")
    
    try:
        from data_fetcher import StockDataFetcher
        fetcher = StockDataFetcher()
        
        # 测试获取股票列表
        stocks = fetcher.get_all_stocks_with_market_cap()
        if stocks.empty:
            print("❌ 无法获取股票列表")
            return False
        
        print(f"✅ 成功获取 {len(stocks)} 只股票")
        return True
    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return False

def test_strategies():
    """测试策略运行"""
    print("\n🔍 测试策略运行...")
    
    strategies = ['technical', 'comprehensive']
    
    for strategy in strategies:
        print(f"\n   测试 {strategy} 策略...")
        try:
            # 运行策略（限制数据量以加快测试）
            result = subprocess.run(
                ['python', 'main.py', 'select', '--strategy', strategy],
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            if result.returncode == 0:
                print(f"   ✅ {strategy} 策略运行成功")
            else:
                print(f"   ❌ {strategy} 策略运行失败")
                print(f"   错误输出: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⚠️ {strategy} 策略运行超时")
            return False
        except Exception as e:
            print(f"   ❌ {strategy} 策略运行异常: {e}")
            return False
    
    return True

def test_output_files():
    """测试输出文件生成"""
    print("\n🔍 测试输出文件...")
    
    today = datetime.now().strftime('%Y-%m-%d')
    expected_files = [
        f'results/technical_selection_{today}.json',
        f'results/comprehensive_selection_{today}.json'
    ]
    
    for file_path in expected_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
            # 检查文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                print(f"      包含 {len(data)} 条记录")
            except Exception as e:
                print(f"      ⚠️ 文件格式错误: {e}")
        else:
            print(f"   ❌ {file_path} 不存在")
            return False
    
    return True

def main():
    """主测试函数"""
    print("🚀 开始 GitHub Actions 环境测试")
    print("=" * 50)
    
    tests = [
        ("环境配置", test_environment),
        ("模块导入", test_imports),
        ("数据获取", test_data_fetcher),
        ("策略运行", test_strategies),
        ("输出文件", test_output_files)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 项测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！GitHub Actions 应该能正常运行")
        return True
    else:
        print("⚠️ 部分测试失败，需要修复问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 