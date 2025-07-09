#!/usr/bin/env python3
"""
Web界面应用
提供选股结果的Web展示界面
"""

try:
    from flask import Flask, render_template, jsonify, request
except ImportError:
    print("Flask未安装，请运行: pip install flask")
    exit(1)

import json
import os
from datetime import datetime, timedelta

# 导入新的策略化结构
from strategies.technical_strategy import TechnicalStrategySelector
from strategies.comprehensive_strategy import ComprehensiveStrategySelector
from core.config import config

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = config.WEB_CONFIG['secret_key']

# 策略映射
STRATEGY_MAP = {
    'technical': TechnicalStrategySelector,
    'comprehensive': ComprehensiveStrategySelector,
}

@app.route('/')
def index():
    """主页 - 显示选股结果，支持策略切换"""
    # 从查询参数获取策略，默认为 'technical'
    strategy_name = request.args.get('strategy', 'technical')
    if strategy_name not in STRATEGY_MAP:
        strategy_name = 'technical'

    today = datetime.now().strftime('%Y-%m-%d')
    results = load_results(today, strategy_name)
    
    # 渲染主模板
    return render_template('dashboard.html', 
                           results=results, 
                           today=today,
                           current_strategy=strategy_name,
                           strategies=STRATEGY_MAP.keys(),
                           app_name=config.APP_NAME)

@app.route('/api/run_selection', methods=['POST'])
def api_run_selection():
    """API接口 - 手动触发指定策略的选股"""
    # 使用 silent=True 避免因无效 JSON 直接抛出 400 错误
    data = request.get_json(silent=True) or {}
    strategy_name = data.get('strategy')

    if not strategy_name or strategy_name not in STRATEGY_MAP:
        return jsonify({'success': False, 'error': '无效的策略名称'}), 400

    try:
        # 先做一次快速数据源可用性检查（如无法获取股票列表则立即返回错误提示）
        from data_fetcher import StockDataFetcher
        try:
            test_fetcher = StockDataFetcher()
            test_df = test_fetcher.get_all_stocks_with_market_cap()
            if test_df is None or test_df.empty:
                return jsonify({'success': False, 'error': '无法获取股票列表，可能是网络或数据源问题。请稍后重试。'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': f'数据源检查失败: {str(e)}'}), 500

        # 在后台线程中执行选股，防止阻塞
        import threading
        def run_async():
            strategy_class = STRATEGY_MAP[strategy_name]
            selector = strategy_class()
            selector.run_selection()
        
        thread = threading.Thread(target=run_async)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': f'策略 [{strategy_name}] 已在后台启动，请稍后刷新页面查看结果。'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def load_results(date, strategy_name):
    """根据策略名称和日期加载结果文件"""
    # 新的文件名格式: {strategy_name}_selection_{date}.json
    filename = f"results/{strategy_name}_selection_{date}.json"
    
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载结果文件 {filename} 失败: {e}")
        return None

def create_templates_if_not_exist():
    """如果模板文件不存在，则创建它们"""
    templates_dir = 'templates'
    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    dashboard_path = os.path.join(templates_dir, 'dashboard.html')
    
    if not os.path.exists(dashboard_path):
        dashboard_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .stock-card { border-left-width: 5px; }
        .stock-card.top-1 { border-left-color: #ffc107; } /* Gold */
        .stock-card.top-2 { border-left-color: #ced4da; } /* Silver */
        .stock-card.top-3 { border-left-color: #cd7f32; } /* Bronze */
    </style>
</head>
<body>
    <div class="container py-4">
        <header class="pb-3 mb-4 border-bottom">
            <h1 class="fs-4">{{ app_name }} - {{ current_strategy | capitalize }} 策略</h1>
        </header>

        <div class="p-5 mb-4 bg-light rounded-3">
            <div class="container-fluid py-5">
                <h1 class="display-5 fw-bold">今日选股推荐</h1>
                <p class="col-md-8 fs-4">日期: {{ today }}</p>
                <div class="d-flex gap-2">
                    <button class="btn btn-primary btn-lg" type="button" onclick="runSelection()">立即执行选股</button>
                    <div class="dropdown">
                        <a class="btn btn-secondary btn-lg dropdown-toggle" href="#" role="button" id="strategyDropdown" data-bs-toggle="dropdown" aria-expanded="false">
                            切换策略
                        </a>
                        <ul class="dropdown-menu" aria-labelledby="strategyDropdown">
                            {% for strategy in strategies %}
                            <li><a class="dropdown-item {% if strategy == current_strategy %}active{% endif %}" href="/?strategy={{ strategy }}">{{ strategy | capitalize }}</a></li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            </div>
        </div>
        
        {% if results and results.stocks %}
            <div class="row row-cols-1 row-cols-md-2 g-4">
                {% for stock in results.stocks %}
                <div class="col">
                    <div class="card h-100 stock-card top-{{ loop.index }}">
                        <div class="card-body">
                            <h5 class="card-title d-flex justify-content-between">
                                <span>
                            {% if loop.index == 1 %}🥇{% elif loop.index == 2 %}🥈{% elif loop.index == 3 %}🥉{% else %}#{{ loop.index }}{% endif %}
                            {{ stock.name }} ({{ stock.code }})
                                </span>
                                <span class="badge bg-primary rounded-pill">{{ stock.score }}/100</span>
                            </h5>
                            <p class="card-text">
                                <strong>当前价格:</strong> ¥{{ stock.current_price | round(2) }} | 
                                <strong>市值:</strong> {{ (stock.market_cap / 100000000) | round(1) }}亿
                            </p>
                            {% if stock.reasons %}
                            <p class="card-text"><small class="text-muted">推荐理由: {{ stock.reasons | join(' + ') }}</small></p>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        {% else %}
            <div class="alert alert-warning" role="alert">
                <h4 class="alert-heading">暂无推荐股票</h4>
                <p>今日使用 [{{ current_strategy }}] 策略暂未筛选出符合条件的股票。您可以尝试执行选股或切换策略查看。</p>
            </div>
        {% endif %}
        
        <footer class="pt-3 mt-4 text-muted border-top">
            ⚠️ 风险提示: 本平台仅提供数据分析工具，不构成任何投资建议。股市有风险，投资需谨慎。
        </footer>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function runSelection() {
            alert('将在后台执行 [{{ current_strategy }}] 策略，请稍后刷新页面查看结果。');
            fetch('/api/run_selection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ strategy: '{{ current_strategy }}' })
            })
            .then(response => response.json())
            .then(data => {
                if (!data.success) {
                    alert('执行失败: ' + data.error);
                }
            });
        }
    </script>
</body>
</html>
"""
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(dashboard_template)
        print(f"✅ 创建了新的 dashboard.html 模板。")

if __name__ == '__main__':
    create_templates_if_not_exist()
    app.run(debug=config.DEBUG, port=5000) 