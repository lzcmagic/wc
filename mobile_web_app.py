#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动端智能选股Web应用
支持响应式设计、PWA、暗色模式等现代特性
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import json
import os
from datetime import datetime, timedelta
import logging
from full_market_scanner import FullMarketScanner
from advanced_indicators import AdvancedIndicators
from notification_manager import NotificationManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'mobile_stock_app_2025'

# 创建必要的目录
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)
os.makedirs('static/icons', exist_ok=True)

# 全局对象
scanner = FullMarketScanner()
indicators = AdvancedIndicators()
notification_manager = NotificationManager()

@app.route('/')
def index():
    """首页 - 移动端优化"""
    return render_template('mobile_index.html')

@app.route('/api/scan')
def api_scan():
    """API: 执行选股扫描"""
    try:
        min_score = int(request.args.get('min_score', 60))
        max_results = int(request.args.get('max_results', 20))
        sample_size = int(request.args.get('sample_size', 300))
        
        results = scanner.scan_full_market(
            min_score=min_score,
            max_results=max_results,
            sample_size=sample_size
        )
        
        return jsonify({
            'status': 'success',
            'data': results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"API扫描错误: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/stock/<stock_code>')
def api_stock_detail(stock_code):
    """API: 获取股票详细分析"""
    try:
        # 这里需要实现单个股票的详细分析
        # 暂时返回模拟数据
        return jsonify({
            'status': 'success',
            'data': {
                'code': stock_code,
                'name': '示例股票',
                'price': 10.50,
                'change_percent': 2.5,
                'analysis': '技术分析结果'
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/notification/test')
def api_test_notification():
    """API: 测试通知功能"""
    try:
        test_stocks = [{
            'name': '测试股票',
            'code': '000001',
            'price': 10.50,
            'change_percent': 2.5,
            'score': 85,
            'market_cap': '100亿',
            'reasons': '技术指标良好 | 成交量放大'
        }]
        
        results = notification_manager.send_daily_report(test_stocks, "📱 移动端测试通知")
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/manifest.json')
def manifest():
    """PWA清单文件"""
    return jsonify({
        "name": "智能选股系统",
        "short_name": "选股助手",
        "description": "AI驱动的A股智能选股系统",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#1a1a1a",
        "theme_color": "#667eea",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    })

@app.route('/sw.js')
def service_worker():
    """Service Worker for PWA"""
    return send_from_directory('static/js', 'sw.js')

def create_mobile_templates():
    """创建移动端模板文件"""
    
    # 创建主页模板
    mobile_index_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#667eea">
    <title>智能选股系统</title>
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" type="image/png" href="/static/icons/icon-192.png">
    <link rel="apple-touch-icon" href="/static/icons/icon-192.png">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --primary-color: #667eea;
            --secondary-color: #764ba2;
            --bg-color: #f8f9fa;
            --card-bg: #ffffff;
            --text-color: #333333;
            --text-secondary: #666666;
            --border-color: #e0e0e0;
            --success-color: #4caf50;
            --warning-color: #ff9800;
            --error-color: #f44336;
        }
        
        [data-theme="dark"] {
            --bg-color: #121212;
            --card-bg: #1e1e1e;
            --text-color: #ffffff;
            --text-secondary: #aaaaaa;
            --border-color: #333333;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            transition: all 0.3s ease;
        }
        
        .header {
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 1rem;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            font-size: 1.4rem;
            margin-bottom: 0.5rem;
        }
        
        .header-controls {
            display: flex;
            justify-content: center;
            gap: 1rem;
            margin-top: 1rem;
        }
        
        .btn {
            background: rgba(255,255,255,0.2);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.9rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .btn:hover, .btn:active {
            background: rgba(255,255,255,0.3);
            transform: translateY(-1px);
        }
        
        .btn-primary {
            background: var(--primary-color);
            border: none;
            color: white;
        }
        
        .container {
            padding: 1rem;
            max-width: 100%;
            margin: 0 auto;
        }
        
        .scan-controls {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color);
        }
        
        .control-group {
            margin-bottom: 1rem;
        }
        
        .control-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: var(--text-color);
        }
        
        .slider-container {
            position: relative;
            margin: 1rem 0;
        }
        
        .slider {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: var(--border-color);
            outline: none;
            -webkit-appearance: none;
        }
        
        .slider::-webkit-slider-thumb {
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: var(--primary-color);
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: var(--primary-color);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .slider-value {
            position: absolute;
            right: 0;
            top: -25px;
            background: var(--primary-color);
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8rem;
            font-weight: bold;
        }
        
        .scan-btn {
            width: 100%;
            background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
            border: none;
            color: white;
            padding: 1rem;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        
        .scan-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .scan-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 2rem;
        }
        
        .spinner {
            border: 3px solid var(--border-color);
            border-top: 3px solid var(--primary-color);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 1rem;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .results {
            margin-top: 1rem;
        }
        
        .stock-card {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color);
            transition: all 0.3s ease;
        }
        
        .stock-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .stock-name {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--text-color);
        }
        
        .stock-code {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        
        .stock-score {
            background: var(--success-color);
            color: white;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .stock-price {
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--primary-color);
        }
        
        .stock-change {
            font-size: 0.9rem;
            font-weight: 600;
        }
        
        .change-positive {
            color: var(--success-color);
        }
        
        .change-negative {
            color: var(--error-color);
        }
        
        .stock-reasons {
            margin-top: 0.8rem;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        
        .reason-tag {
            background: rgba(102, 126, 234, 0.1);
            color: var(--primary-color);
            padding: 0.3rem 0.8rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 500;
            border: 1px solid rgba(102, 126, 234, 0.2);
        }
        
        .stats-bar {
            background: var(--card-bg);
            border-radius: 15px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border: 1px solid var(--border-color);
            display: flex;
            justify-content: space-around;
            text-align: center;
        }
        
        .stat-item {
            flex: 1;
        }
        
        .stat-value {
            font-size: 1.4rem;
            font-weight: 700;
            color: var(--primary-color);
        }
        
        .stat-label {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 0.2rem;
        }
        
        .theme-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: var(--primary-color);
            border: none;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            z-index: 1000;
        }
        
        .theme-toggle:hover {
            transform: scale(1.1);
        }
        
        .empty-state {
            text-align: center;
            padding: 3rem 1rem;
            color: var(--text-secondary);
        }
        
        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        @media (max-width: 480px) {
            .container {
                padding: 0.5rem;
            }
            
            .scan-controls {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 1.2rem;
            }
            
            .header-controls {
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .btn {
                padding: 0.4rem 0.8rem;
                font-size: 0.8rem;
            }
            
            .stock-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }
        }
        
        /* PWA相关样式 */
        .install-prompt {
            background: var(--primary-color);
            color: white;
            padding: 1rem;
            text-align: center;
            display: none;
        }
        
        .install-prompt.show {
            display: block;
        }
        
        .install-btn {
            background: white;
            color: var(--primary-color);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-weight: 600;
            cursor: pointer;
            margin-left: 1rem;
        }
    </style>
</head>
<body>
    <div class="install-prompt" id="installPrompt">
        <span>📱 安装选股助手到桌面，获得更好的体验！</span>
        <button class="install-btn" id="installBtn">安装</button>
        <button class="install-btn" id="dismissBtn">取消</button>
    </div>
    
    <div class="header">
        <h1>🏆 智能选股系统</h1>
        <p>AI驱动的A股精选推荐</p>
        <div class="header-controls">
            <button class="btn" onclick="testNotification()">📱 测试通知</button>
            <button class="btn" onclick="toggleSettings()">⚙️ 设置</button>
        </div>
    </div>
    
    <div class="container">
        <div class="scan-controls">
            <div class="control-group">
                <label for="minScore">最低评分</label>
                <div class="slider-container">
                    <input type="range" id="minScore" class="slider" min="50" max="90" value="60" step="5">
                    <div class="slider-value" id="minScoreValue">60分</div>
                </div>
            </div>
            
            <div class="control-group">
                <label for="maxResults">推荐数量</label>
                <div class="slider-container">
                    <input type="range" id="maxResults" class="slider" min="10" max="50" value="20" step="5">
                    <div class="slider-value" id="maxResultsValue">20只</div>
                </div>
            </div>
            
            <div class="control-group">
                <label for="sampleSize">扫描规模</label>
                <div class="slider-container">
                    <input type="range" id="sampleSize" class="slider" min="100" max="1000" value="300" step="100">
                    <div class="slider-value" id="sampleSizeValue">300只</div>
                </div>
            </div>
            
            <button class="scan-btn" id="scanBtn" onclick="startScan()">
                🚀 开始扫描
            </button>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>正在扫描全市场股票...</p>
            <p id="scanProgress">准备中...</p>
        </div>
        
        <div class="stats-bar" id="statsBar" style="display: none;">
            <div class="stat-item">
                <div class="stat-value" id="scanTime">0</div>
                <div class="stat-label">耗时(秒)</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="totalScanned">0</div>
                <div class="stat-label">已扫描</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" id="foundStocks">0</div>
                <div class="stat-label">发现股票</div>
            </div>
        </div>
        
        <div class="results" id="results">
            <div class="empty-state">
                <div class="empty-state-icon">📊</div>
                <h3>准备开始智能选股</h3>
                <p>点击上方按钮开始扫描全市场股票</p>
            </div>
        </div>
    </div>
    
    <button class="theme-toggle" id="themeToggle" onclick="toggleTheme()">🌙</button>
    
    <script>
        // PWA安装
        let deferredPrompt;
        
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            document.getElementById('installPrompt').classList.add('show');
        });
        
        document.getElementById('installBtn').addEventListener('click', async () => {
            if (deferredPrompt) {
                deferredPrompt.prompt();
                const { outcome } = await deferredPrompt.userChoice;
                deferredPrompt = null;
                document.getElementById('installPrompt').classList.remove('show');
            }
        });
        
        document.getElementById('dismissBtn').addEventListener('click', () => {
            document.getElementById('installPrompt').classList.remove('show');
        });
        
        // Service Worker注册
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }
        
        // 主题切换
        function toggleTheme() {
            const body = document.body;
            const themeToggle = document.getElementById('themeToggle');
            
            if (body.getAttribute('data-theme') === 'dark') {
                body.removeAttribute('data-theme');
                themeToggle.textContent = '🌙';
                localStorage.setItem('theme', 'light');
            } else {
                body.setAttribute('data-theme', 'dark');
                themeToggle.textContent = '☀️';
                localStorage.setItem('theme', 'dark');
            }
        }
        
        // 加载保存的主题
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.setAttribute('data-theme', 'dark');
            document.getElementById('themeToggle').textContent = '☀️';
        }
        
        // 滑块事件
        const sliders = {
            minScore: { element: document.getElementById('minScore'), display: document.getElementById('minScoreValue'), suffix: '分' },
            maxResults: { element: document.getElementById('maxResults'), display: document.getElementById('maxResultsValue'), suffix: '只' },
            sampleSize: { element: document.getElementById('sampleSize'), display: document.getElementById('sampleSizeValue'), suffix: '只' }
        };
        
        Object.values(sliders).forEach(slider => {
            slider.element.addEventListener('input', function() {
                slider.display.textContent = this.value + slider.suffix;
            });
        });
        
        // 扫描功能
        async function startScan() {
            const scanBtn = document.getElementById('scanBtn');
            const loading = document.getElementById('loading');
            const results = document.getElementById('results');
            const statsBar = document.getElementById('statsBar');
            
            const minScore = document.getElementById('minScore').value;
            const maxResults = document.getElementById('maxResults').value;
            const sampleSize = document.getElementById('sampleSize').value;
            
            scanBtn.disabled = true;
            scanBtn.textContent = '扫描中...';
            loading.style.display = 'block';
            results.innerHTML = '';
            statsBar.style.display = 'none';
            
            const startTime = Date.now();
            
            try {
                const response = await fetch(`/api/scan?min_score=${minScore}&max_results=${maxResults}&sample_size=${sampleSize}`);
                const data = await response.json();
                
                if (data.status === 'success') {
                    const endTime = Date.now();
                    const scanTime = Math.round((endTime - startTime) / 1000);
                    
                    displayResults(data.data, scanTime, sampleSize);
                } else {
                    throw new Error(data.message);
                }
            } catch (error) {
                console.error('扫描失败:', error);
                results.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">❌</div>
                        <h3>扫描失败</h3>
                        <p>${error.message}</p>
                    </div>
                `;
            } finally {
                scanBtn.disabled = false;
                scanBtn.textContent = '🚀 开始扫描';
                loading.style.display = 'none';
            }
        }
        
        function displayResults(stocks, scanTime, totalScanned) {
            const results = document.getElementById('results');
            const statsBar = document.getElementById('statsBar');
            
            // 更新统计信息
            document.getElementById('scanTime').textContent = scanTime;
            document.getElementById('totalScanned').textContent = totalScanned;
            document.getElementById('foundStocks').textContent = stocks.length;
            statsBar.style.display = 'flex';
            
            if (stocks.length === 0) {
                results.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">📉</div>
                        <h3>未发现符合条件的股票</h3>
                        <p>尝试降低评分要求或调整扫描参数</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            stocks.forEach((stock, index) => {
                const changeClass = stock.change_percent >= 0 ? 'change-positive' : 'change-negative';
                const changeSymbol = stock.change_percent >= 0 ? '+' : '';
                
                const reasons = stock.reasons ? stock.reasons.split(' | ') : [];
                const reasonTags = reasons.map(reason => 
                    `<span class="reason-tag">${reason.trim()}</span>`
                ).join('');
                
                html += `
                    <div class="stock-card" onclick="showStockDetail('${stock.code}')">
                        <div class="stock-header">
                            <div>
                                <div class="stock-name">#${index + 1} ${stock.name}</div>
                                <div class="stock-code">${stock.code}</div>
                            </div>
                            <div class="stock-score">${stock.score}分</div>
                        </div>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                            <div>
                                <span class="stock-price">¥${stock.price.toFixed(2)}</span>
                                <span class="stock-change ${changeClass}">
                                    ${changeSymbol}${stock.change_percent.toFixed(2)}%
                                </span>
                            </div>
                            <div style="font-size: 0.9rem; color: var(--text-secondary);">
                                💰 ${stock.market_cap || 'N/A'}
                            </div>
                        </div>
                        <div class="stock-reasons">
                            ${reasonTags}
                        </div>
                    </div>
                `;
            });
            
            results.innerHTML = html;
        }
        
        function showStockDetail(stockCode) {
            // 这里可以实现股票详情页面
            alert(`查看 ${stockCode} 详细分析（功能开发中）`);
        }
        
        async function testNotification() {
            try {
                const response = await fetch('/api/notification/test');
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('✅ 测试通知发送成功！请检查您的邮箱/微信/钉钉');
                } else {
                    alert('❌ 测试通知发送失败：' + data.message);
                }
            } catch (error) {
                alert('❌ 通知测试失败：' + error.message);
            }
        }
        
        function toggleSettings() {
            alert('⚙️ 设置功能开发中...');
        }
        
        // 添加下拉刷新功能
        let startY = 0;
        let currentY = 0;
        let pullToRefreshEnabled = false;
        
        document.addEventListener('touchstart', function(e) {
            if (window.scrollY === 0) {
                startY = e.touches[0].clientY;
                pullToRefreshEnabled = true;
            }
        });
        
        document.addEventListener('touchmove', function(e) {
            if (!pullToRefreshEnabled) return;
            
            currentY = e.touches[0].clientY;
            if (currentY > startY + 100) {
                // 触发刷新
                e.preventDefault();
                location.reload();
            }
        });
        
        document.addEventListener('touchend', function() {
            pullToRefreshEnabled = false;
        });
    </script>
</body>
</html>'''
    
    with open('templates/mobile_index.html', 'w', encoding='utf-8') as f:
        f.write(mobile_index_html)
    
    # 创建Service Worker
    sw_js = '''
const CACHE_NAME = 'stock-app-v1';
const urlsToCache = [
    '/',
    '/static/css/mobile.css',
    '/static/js/app.js',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png'
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                return cache.addAll(urlsToCache);
            })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    return response;
                }
                return fetch(event.request);
            }
        )
    );
});
'''
    
    with open('static/js/sw.js', 'w', encoding='utf-8') as f:
        f.write(sw_js)
    
    print("✅ 移动端模板创建成功!")

def main():
    """启动移动端Web应用"""
    create_mobile_templates()
    
    print("📱 移动端智能选股Web应用")
    print("="*50)
    print("🚀 启动中...")
    print("📱 支持响应式设计")
    print("🔔 支持PWA安装")
    print("🌙 支持暗色模式")
    print("📊 支持实时扫描")
    print("💬 支持推送通知")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == "__main__":
    main() 