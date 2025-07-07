"""
个人选股系统 Web 界面
提供简单的网页查看选股结果
"""

try:
    from flask import Flask, render_template_string, jsonify
except ImportError:
    print("Flask未安装，请运行: pip install flask")
    exit(1)

import json
import os
from datetime import datetime

# 初始化Flask应用
app = Flask(__name__)
app.secret_key = Config.WEB_CONFIG['secret_key']

# 全局变量
selector = PersonalStockSelector(Config.STOCK_FILTER)

@app.route('/')
def index():
    """主页 - 显示今日推荐"""
    today = datetime.now().strftime('%Y-%m-%d')
    results = load_results(today)
    
    # 简单的HTML模板
    template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>📈 个人A股选股系统</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }
            .header { text-align: center; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 20px; }
            .stock-card { background: #f8f9fa; margin: 15px 0; padding: 15px; border-radius: 8px; border-left: 5px solid #3498db; }
            .stock-name { font-size: 18px; font-weight: bold; color: #2c3e50; }
            .stock-score { background: #e74c3c; color: white; padding: 5px 10px; border-radius: 15px; display: inline-block; }
            .warning { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 今日选股推荐</h1>
                <p>日期: {{ today }}</p>
            </div>
            
            {% if results and results.stocks %}
                {% for stock in results.stocks %}
                <div class="stock-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div class="stock-name">
                            {% if loop.index == 1 %}🥇{% elif loop.index == 2 %}🥈{% elif loop.index == 3 %}🥉{% else %}#{{ loop.index }}{% endif %}
                            {{ stock.name }} ({{ stock.code }})
                        </div>
                        <div class="stock-score">{{ stock.score }}/100</div>
                    </div>
                    <p><strong>当前价格:</strong> ¥{{ stock.current_price }}</p>
                    <p><strong>市值:</strong> {{ "%.0f"|format(stock.market_cap/100000000) }}亿</p>
                    <p><strong>近30日涨幅:</strong> {{ "%+.1f"|format(stock.recent_gain) }}%</p>
                    {% if stock.reasons %}
                    <p><strong>推荐理由:</strong> {{ stock.reasons|join(' + ') }}</p>
                    {% endif %}
                </div>
                {% endfor %}
                
                <div style="text-align: center; margin: 20px 0;">
                    <p><strong>推荐股票数:</strong> {{ results.stocks|length }} 只 | 
                       <strong>平均评分:</strong> {{ results.summary.avg_score }}/100</p>
                </div>
            {% else %}
                <div style="text-align: center; padding: 60px; color: #7f8c8d;">
                    <h3>📭 暂无推荐股票</h3>
                    <p>今日暂无符合条件的推荐股票</p>
                </div>
            {% endif %}
            
            <div class="warning">
                <strong>⚠️ 风险提示:</strong><br>
                本推荐仅基于技术分析，不构成投资建议。股市有风险，投资需谨慎。
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(template, results=results, today=today)

@app.route('/api/results/<date>')
def api_results(date):
    """API接口 - 获取指定日期的选股结果"""
    try:
        results = load_results(date)
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/run_selection', methods=['POST'])
def api_run_selection():
    """API接口 - 手动触发选股"""
    try:
        # 在后台线程中执行选股
        def run_async():
            selector.daily_stock_selection()
        
        thread = threading.Thread(target=run_async)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '选股任务已启动，请稍后刷新页面查看结果'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/history')
def history():
    """历史记录页面"""
    # 获取最近7天的结果
    history_data = []
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        results = load_results(date)
        if results:
            history_data.append({
                'date': date,
                'count': len(results.get('stocks', [])),
                'avg_score': results.get('summary', {}).get('avg_score', 0)
            })
    
    return render_template('history.html', 
                         history=history_data,
                         app_name=Config.APP_NAME)

@app.route('/api/history/<int:days>')
def api_history(days):
    """API接口 - 获取历史数据"""
    try:
        history_data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            results = load_results(date)
            if results:
                history_data.append({
                    'date': date,
                    'stocks': results.get('stocks', []),
                    'summary': results.get('summary', {})
                })
        
        return jsonify({
            'success': True,
            'data': history_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def load_results(date):
    """加载指定日期的选股结果"""
    filename = f"results/stock_selection_{date}.json"
    
    if not os.path.exists(filename):
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载结果文件失败: {e}")
        return None

# 创建模板文件
def create_templates():
    """创建HTML模板文件"""
    # 创建templates目录
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # 主页模板
    dashboard_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ app_name }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .date-info {
            background: #ecf0f1;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
            color: #7f8c8d;
        }
        .stock-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stock-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            border-left: 5px solid #3498db;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .stock-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .stock-name {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
        }
        .stock-score {
            background: #e74c3c;
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-weight: bold;
            font-size: 14px;
        }
        .stock-details {
            margin: 8px 0;
            color: #34495e;
        }
        .stock-price {
            font-size: 20px;
            font-weight: bold;
            color: #27ae60;
        }
        .stock-reasons {
            background: #d5f4e6;
            color: #27ae60;
            padding: 8px 12px;
            border-radius: 5px;
            margin-top: 10px;
            font-size: 14px;
        }
        .actions {
            text-align: center;
            margin: 30px 0;
        }
        .btn {
            background: #3498db;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 0 10px;
            transition: background 0.3s;
        }
        .btn:hover {
            background: #2980b9;
        }
        .btn-success {
            background: #27ae60;
        }
        .btn-success:hover {
            background: #229954;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 15px;
            border-radius: 5px;
            margin-top: 30px;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #7f8c8d;
        }
        .empty-state h3 {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 {{ app_name }}</h1>
        </div>
        
        <div class="date-info">
            <strong>日期:</strong> {{ today }}
        </div>
        
        <div class="actions">
            <button class="btn" onclick="window.location.reload()">🔄 刷新页面</button>
            <button class="btn btn-success" onclick="runSelection()">▶️ 立即选股</button>
            <button class="btn" onclick="window.location.href='/history'">📊 历史记录</button>
        </div>
        
        {% if results and results.stocks %}
            <div class="stock-grid">
                {% for stock in results.stocks %}
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-name">
                            {% if loop.index == 1 %}🥇{% elif loop.index == 2 %}🥈{% elif loop.index == 3 %}🥉{% else %}#{{ loop.index }}{% endif %}
                            {{ stock.name }} ({{ stock.code }})
                        </div>
                        <div class="stock-score">{{ stock.score }}/100</div>
                    </div>
                    
                    <div class="stock-details">
                        <div class="stock-price">¥{{ stock.current_price }}</div>
                    </div>
                    
                    <div class="stock-details">
                        <strong>市值:</strong> {{ "%.0f"|format(stock.market_cap/100000000) }}亿
                    </div>
                    
                    <div class="stock-details">
                        <strong>近30日涨幅:</strong> 
                        <span style="color: {% if stock.recent_gain > 0 %}#e74c3c{% else %}#27ae60{% endif %}">
                            {{ "%+.1f"|format(stock.recent_gain) }}%
                        </span>
                    </div>
                    
                    {% if stock.reasons %}
                    <div class="stock-reasons">
                        <strong>推荐理由:</strong> {{ stock.reasons|join(' + ') }}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            
            <div style="text-align: center; margin: 20px 0; color: #7f8c8d;">
                <p><strong>推荐股票数:</strong> {{ results.stocks|length }} 只</p>
                <p><strong>平均评分:</strong> {{ results.summary.avg_score }}/100</p>
            </div>
        {% else %}
            <div class="empty-state">
                <h3>📭 暂无推荐股票</h3>
                <p>今日暂无符合条件的推荐股票，或者尚未执行选股分析。</p>
                <button class="btn btn-success" onclick="runSelection()">立即执行选股</button>
            </div>
        {% endif %}
        
        <div class="warning">
            <strong>⚠️ 风险提示:</strong><br>
            本推荐仅基于技术分析，不构成投资建议。股市有风险，投资需谨慎，请结合基本面分析和个人风险承受能力。
        </div>
    </div>
    
    <script>
        function runSelection() {
            if (confirm('确定要立即执行选股分析吗？这可能需要几分钟时间。')) {
                fetch('/api/run_selection', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert(data.message);
                    } else {
                        alert('执行失败: ' + data.error);
                    }
                })
                .catch(error => {
                    alert('请求失败: ' + error);
                });
            }
        }
    </script>
</body>
</html>'''
    
    # 历史记录模板
    history_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>历史记录 - {{ app_name }}</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .history-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .history-table th, .history-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .history-table th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
        }
        .history-table tr:hover {
            background-color: #f5f5f5;
        }
        .btn {
            background: #3498db;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
        }
        .btn:hover {
            background: #2980b9;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #7f8c8d;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 历史记录</h1>
        </div>
        
        <div style="text-align: center; margin-bottom: 20px;">
            <a href="/" class="btn">← 返回主页</a>
        </div>
        
        {% if history %}
            <table class="history-table">
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>推荐股票数</th>
                        <th>平均评分</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in history %}
                    <tr>
                        <td>{{ item.date }}</td>
                        <td>{{ item.count }} 只</td>
                        <td>{{ item.avg_score }}/100</td>
                        <td>
                            <a href="/api/results/{{ item.date }}" target="_blank" class="btn">查看详情</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        {% else %}
            <div class="empty-state">
                <h3>📭 暂无历史记录</h3>
                <p>还没有历史选股记录，请先执行选股分析。</p>
                <a href="/" class="btn">返回主页</a>
            </div>
        {% endif %}
    </div>
</body>
</html>'''
    
    # 写入模板文件
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)
    
    with open('templates/history.html', 'w', encoding='utf-8') as f:
        f.write(history_template)
    
    print("HTML模板文件已创建")

def main():
    """启动Web应用"""
    # 初始化配置
    init_config()
    
    # 创建模板文件
    create_templates()
    
    print(f"启动 {Config.APP_NAME} Web界面...")
    print(f"访问地址: http://{Config.WEB_CONFIG['host']}:{Config.WEB_CONFIG['port']}")
    
    # 启动Flask应用
    app.run(
        host=Config.WEB_CONFIG['host'],
        port=Config.WEB_CONFIG['port'],
        debug=Config.WEB_CONFIG['debug']
    )

if __name__ == '__main__':
    main() 