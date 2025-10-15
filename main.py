from flask import Flask, make_response, request, jsonify
import requests as r
import datetime as dt
import time as t
import json

app = Flask(__name__)

# 性能数据收集路由
@app.route('/collect-metrics', methods=['POST'])
def collect_metrics():
    try:
        if not request.is_json:
            return jsonify({
                'status': 'error',
                'message': 'Content-Type must be application/json'
            }), 415
            
        metrics_data = request.get_json()
        
        # 更新性能指标
        if metrics_data.get('deviceType') in performance_metrics['device_stats']:
            performance_metrics['device_stats'][metrics_data['deviceType']] += 1
        
        if metrics_data.get('connection', {}).get('effectiveType'):
            conn_type = metrics_data['connection']['effectiveType']
            if conn_type in performance_metrics['connection_types']:
                performance_metrics['connection_types'][conn_type] += 1
            else:
                performance_metrics['connection_types']['other'] += 1
        
        # 添加性能指标
        if metrics_data.get('ttfb'):
            performance_metrics['ttfb'].append(metrics_data['ttfb'])
        if metrics_data.get('fcp'):
            performance_metrics['fcp'].append(metrics_data['fcp'])
        if metrics_data.get('lcp'):
            performance_metrics['lcp'].append(metrics_data['lcp'])
        if metrics_data.get('fid'):
            performance_metrics['fid'].append(metrics_data['fid'])
        if metrics_data.get('cls'):
            performance_metrics['cls'].append(metrics_data['cls'])
        
        # 记录内存使用情况
        if metrics_data.get('memory'):
            performance_metrics['memory_usage'].append({
                'timestamp': time.time(),
                'used': metrics_data['memory'].get('usedJSHeapSize', 0),
                'total': metrics_data['memory'].get('totalJSHeapSize', 0)
            })
        
        # 记录带宽使用情况
        if metrics_data.get('resourceTiming'):
            total_transfer = sum(
                resource.get('transferSize', 0) 
                for resource in metrics_data['resourceTiming']
            )
            performance_metrics['bandwidth_usage'].append({
                'timestamp': time.time(),
                'bytes': total_transfer
            })
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(f"收集性能指标时出错: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# 缓存配置
CACHE_DURATION = 600  # 缓存10分钟
CACHE_STALE_WHILE_REVALIDATE = 300  # 允许使用过期缓存的时间（5分钟）
cache = {
    'data': None,
    'timestamp': 0,
    'is_revalidating': False,
    'last_error': None,
    'error_count': 0
}

# 性能监控配置
performance_metrics = {
    'api_calls': 0,
    'cache_hits': 0,
    'cache_misses': 0,
    'errors': 0,
    'response_times': [],
    'last_gc_time': 0,
    'device_stats': {
        'mobile': 0,
        'tablet': 0,
        'desktop': 0
    },
    'connection_types': {
        '4g': 0,
        '3g': 0,
        'wifi': 0,
        'other': 0
    },
    'ttfb': [],           # Time to First Byte
    'fcp': [],            # First Contentful Paint
    'lcp': [],            # Largest Contentful Paint
    'fid': [],            # First Input Delay
    'cls': [],            # Cumulative Layout Shift
    'memory_usage': [],   # 内存使用情况
    'bandwidth_usage': []  # 带宽使用情况
}

def get_img_code(a, index=0):
    """根据用户头像ID生成头像HTML，使用data URL作为默认图片"""
    # 默认头像的 data URL（一个简单的灰色圆圈SVG）
    default_img = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiNlMGUwZTAiLz48L3N2Zz4="
    
    if a == "None":
        img_url = default_img
    else:
        img_url = f"https://abc.520gxx.com/static/internalapi/asset/{a}"
    
    # 根据索引设置加载优先级
    priority = "high" if index < 3 else "low"
    loading = "eager" if index < 3 else "lazy"
    
    return f'''<div class="media-left">
      <figure class="image is-32x32 image is-1by1">
        <img class="is-rounded" 
             loading="{loading}"
             decoding="async" 
             fetchpriority="{priority}"
             src="{img_url}"
             width="32"
             height="32"
             alt="用户头像"
             onload="this.classList.add('loaded')"
             onerror="this.src='{default_img}'">
        <noscript>
          <img class="is-rounded" 
               src="{default_img}" 
               width="32" 
               height="32" 
               alt="用户头像">
        </noscript>
      </figure>
    </div>'''

def get_members_data():
    """从API获取成员数据，带高级缓存机制、错误重试和性能监控"""
    current_time = t.time()
    
    # 性能监控 - 定期清理
    if current_time - performance_metrics['last_gc_time'] > 3600:  # 每小时清理一次
        performance_metrics['response_times'] = performance_metrics['response_times'][-1000:]  # 保留最近1000条
        performance_metrics['last_gc_time'] = current_time
    
    # 检查缓存状态
    cache_age = current_time - cache['timestamp']
    cache_valid = cache['data'] is not None and cache_age < CACHE_DURATION
    cache_stale = cache['data'] is not None and cache_age < (CACHE_DURATION + CACHE_STALE_WHILE_REVALIDATE)
    
    # 如果缓存有效，直接返回
    if cache_valid:
        performance_metrics['cache_hits'] += 1
        return cache['data']
    
    # 如果缓存过期但在允许范围内，后台刷新
    if cache_stale and not cache['is_revalidating']:
        cache['is_revalidating'] = True
        # 在实际环境中，这里应该使用异步任务或线程池
        # 为演示目的，我们仍然同步执行
    
    # 性能监控 - API调用计数
    performance_metrics['api_calls'] += 1
    
    # 获取新数据，添加重试机制
    max_retries = 3
    retry_delay = 1
    last_error = None
    
    for attempt in range(max_retries):
        try:
            start_time = t.time()
            session = r.Session()
            session.headers.update({
                'Accept-Encoding': 'gzip, deflate',
                'Cache-Control': 'max-age=0'
            })
            
            res = session.get("https://api.abc.520gxx.com/studio/user?id=691", timeout=5)
            res.raise_for_status()
            infos = res.json()
            
            # 记录响应时间
            response_time = t.time() - start_time
            performance_metrics['response_times'].append(response_time)
            
            data = ([m["nickname"] for m in infos["data"]], 
                   [m["head"] for m in infos["data"]], 
                   [m["id"] for m in infos["data"]])
            
            # 更新缓存
            cache['data'] = data
            cache['timestamp'] = current_time
            cache['is_revalidating'] = False
            cache['last_error'] = None
            cache['error_count'] = 0
            
            performance_metrics['cache_misses'] += 1
            return data
            
        except Exception as e:
            last_error = e
            cache['error_count'] += 1
            performance_metrics['errors'] += 1
            
            if attempt < max_retries - 1:
                t.sleep(retry_delay * (attempt + 1))
                continue
    
    # 所有重试都失败了
    print(f"API请求错误: {last_error}")
    cache['last_error'] = str(last_error)
    cache['is_revalidating'] = False
    
    # 如果有过期缓存，在错误时仍然返回它
    if cache_stale:
        return cache['data']
    
    return [], [], []

def generate_html(members_list, heads_list, id_list):
    """生成优化后的HTML页面，包含性能监控和渐进式加载"""
    # 性能统计
    avg_response_time = sum(performance_metrics['response_times']) / len(performance_metrics['response_times']) if performance_metrics['response_times'] else 0
    cache_hit_rate = performance_metrics['cache_hits'] / (performance_metrics['cache_hits'] + performance_metrics['cache_misses']) if (performance_metrics['cache_hits'] + performance_metrics['cache_misses']) > 0 else 0
    
    # 获取要预加载的头像
    preload_avatars = heads_list[:3] if heads_list else ["6e2b0b1056aaa08419fb69a3d7aa5727.png"]
    first_avatar_url = f"https://abc.520gxx.com/static/internalapi/asset/{preload_avatars[0]}"
    
    feedback = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>StudioJade网站</title>
    
    <!-- 性能优化元标签 -->
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="StudioJade工作室官方网站">
    <meta name="theme-color" content="#ffffff">
    
    <!-- DNS预加载 -->
    <link rel="preconnect" href="https://s4.zstatic.net" crossorigin>
    <link rel="preconnect" href="https://abc.520gxx.com" crossorigin>
    <link rel="preconnect" href="https://jiashu.jsdmirror.com" crossorigin>
    <link rel="dns-prefetch" href="https://s4.zstatic.net">
    <link rel="dns-prefetch" href="https://abc.520gxx.com">
    <link rel="dns-prefetch" href="https://jiashu.jsdmirror.com">
    
    <!-- 资源预加载 -->
    <link rel="preload" href="https://jiashu.jsdmirror.com/gh/StudioJade/web/logo.webp" as="image" type="image/webp">
    <link rel="preload" href="https://s4.zstatic.net/npm/bulma/css/bulma.min.css" as="style">
    
    <!-- 关键CSS内联 -->
    <style>
        /* 首屏关键样式 */
        :root {
            --safe-area-inset-top: env(safe-area-inset-top, 0px);
            --safe-area-inset-bottom: env(safe-area-inset-bottom, 0px);
        }
        
        /* 基础样式 */
        .media-left { display: flex; align-items: center; }
        .is-rounded { border-radius: 50%; }
        img { max-width: 100%; height: auto; }
        
        /* 移动端优化 */
        @media (max-width: 768px) {
            body {
                padding: var(--safe-area-inset-top) 0 var(--safe-area-inset-bottom);
                touch-action: manipulation;
                -webkit-tap-highlight-color: transparent;
            }
            
            /* 优化点击区域 */
            .navbar-item, button, a {
                min-height: 44px;
                min-width: 44px;
                padding: 12px;
                touch-action: manipulation;
            }
            
            /* 优化字体大小 */
            html {
                font-size: calc(16px + 0.5vw);
                line-height: 1.5;
            }
            
            /* 优化滚动体验 */
            * {
                -webkit-overflow-scrolling: touch;
            }
            
            /* 优化图片大小 */
            .image.is-32x32 {
                width: 48px;
                height: 48px;
            }
            
            /* 响应式导航 */
            .navbar-burger { 
                display: block;
                padding: 16px;
                margin: 0;
            }
            .navbar-menu { 
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #fff;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                padding: 1rem;
                z-index: 1000;
            }
            .navbar-menu.is-active {
                display: block;
                animation: slideDown 0.3s ease-out;
            }
        }
        
        /* 深色模式支持 */
        @media (prefers-color-scheme: dark) {
            body {
                background-color: #121212;
                color: #e0e0e0;
            }
            .navbar-menu {
                background: #1e1e1e;
            }
        }
        
        /* 减少动画 */
        @media (prefers-reduced-motion: reduce) {
            * {
                animation-duration: 0.01ms !important;
                transition-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
            }
        }
        
        /* 加载动画 */
        @keyframes slideDown {
            from { transform: translateY(-100%); }
            to { transform: translateY(0); }
        }
        
        .loading-skeleton {
            background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
            background-size: 200% 100%;
            animation: loading 1.5s infinite;
        }
        
        @keyframes loading {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
    </style>
    
    <!-- 图标 -->
    <link rel="icon" href="https://jiashu.jsdmirror.com/gh/StudioJade/web/logo.webp" type="image/x-icon">
    
    <!-- 非阻塞CSS加载 -->
    <link rel="stylesheet" href="https://s4.zstatic.net/npm/bulma/css/bulma.min.css" 
          media="print" onload="this.media='all'">
    <noscript>
        <link rel="stylesheet" href="https://s4.zstatic.net/npm/bulma/css/bulma.min.css">
    </noscript>
    
    <!-- 资源提示 -->
    <link rel="preload" href="''' + first_avatar_url + '''" as="image">
    
    <!-- 性能监控和设备适配脚本 -->
    <script>
    // 初始化性能监控
    performance.mark('start');
    
    // 性能监控类
    class PerformanceMonitor {
        constructor() {
            this.metrics = {
                ttfb: null,
                fcp: null,
                lcp: null,
                fid: null,
                cls: 0,
                deviceType: this.getDeviceType(),
                connection: this.getConnectionType(),
                memory: {},
                resourceTiming: [],
                errors: []
            };
            
            this.initObservers();
            this.monitorMemory();
            this.monitorErrors();
            this.monitorNetwork();
        }
        
        getDeviceType() {
            const ua = navigator.userAgent;
            if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
                return 'tablet';
            }
            if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated/i.test(ua)) {
                return 'mobile';
            }
            return 'desktop';
        }
        
        getConnectionType() {
            if ('connection' in navigator) {
                const conn = navigator.connection;
                return {
                    effectiveType: conn.effectiveType,
                    saveData: conn.saveData,
                    rtt: conn.rtt,
                    downlink: conn.downlink
                };
            }
            return null;
        }
        
        initObservers() {
            // Web Vitals 监控
            if ('PerformanceObserver' in window) {
                // FCP 监控
                new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    this.metrics.fcp = entries[0].startTime;
                }).observe({ type: 'paint', buffered: true });
                
                // LCP 监控
                new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    this.metrics.lcp = entries[entries.length - 1].startTime;
                }).observe({ type: 'largest-contentful-paint', buffered: true });
                
                // FID 监控
                new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    this.metrics.fid = entries[0].processingStart - entries[0].startTime;
                }).observe({ type: 'first-input', buffered: true });
                
                // CLS 监控
                new PerformanceObserver((list) => {
                    for (const entry of list.getEntries()) {
                        if (!entry.hadRecentInput) {
                            this.metrics.cls += entry.value;
                        }
                    }
                }).observe({ type: 'layout-shift', buffered: true });
                
                // 资源计时
                new PerformanceObserver((list) => {
                    const entries = list.getEntries();
                    this.metrics.resourceTiming = entries.map(entry => ({
                        name: entry.name,
                        duration: entry.duration,
                        transferSize: entry.transferSize
                    }));
                }).observe({ entryTypes: ['resource'] });
            }
            
            // TTFB 计算
            this.metrics.ttfb = performance.timing.responseStart - performance.timing.navigationStart;
        }
        
        monitorMemory() {
            if ('memory' in performance) {
                setInterval(() => {
                    this.metrics.memory = {
                        usedJSHeapSize: performance.memory.usedJSHeapSize,
                        totalJSHeapSize: performance.memory.totalJSHeapSize
                    };
                }, 5000);
            }
        }
        
        monitorErrors() {
            window.addEventListener('error', (event) => {
                this.metrics.errors.push({
                    message: event.message,
                    source: event.filename,
                    line: event.lineno,
                    timestamp: Date.now()
                });
            });
        }
        
        monitorNetwork() {
            if ('connection' in navigator) {
                navigator.connection.addEventListener('change', () => {
                    this.metrics.connection = this.getConnectionType();
                });
            }
        }
        
        sendMetrics() {
            // 发送性能数据到服务器
            const data = {
                ...this.metrics,
                timestamp: Date.now(),
                url: window.location.href
            };
            
            // 使用 fetch 发送数据，确保设置正确的 Content-Type
            fetch('/collect-metrics', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                keepalive: true
            }).catch(error => {
                console.error('发送性能指标失败:', error);
            });
        }
    }
    
    // 初始化性能监控
    const monitor = new PerformanceMonitor();
    
    // 移动端优化
    document.addEventListener('DOMContentLoaded', () => {
        // 处理移动端导航
        const burger = document.querySelector('.navbar-burger');
        const menu = document.querySelector('.navbar-menu');
        if (burger && menu) {
            burger.addEventListener('click', () => {
                menu.classList.toggle('is-active');
                
                // 添加滑动关闭菜单
                let touchStartY = 0;
                menu.addEventListener('touchstart', (e) => {
                    touchStartY = e.touches[0].clientY;
                });
                
                menu.addEventListener('touchmove', (e) => {
                    const touchY = e.touches[0].clientY;
                    const diff = touchStartY - touchY;
                    if (diff > 50) { // 向上滑动50px
                        menu.classList.remove('is-active');
                    }
                });
            });
        }
        
        // 添加图片延迟加载
        if ('loading' in HTMLImageElement.prototype) {
            const images = document.querySelectorAll('img[loading="lazy"]');
            images.forEach(img => {
                // 添加骨架屏
                const placeholder = document.createElement('div');
                placeholder.classList.add('loading-skeleton');
                placeholder.style.width = img.width + 'px';
                placeholder.style.height = img.height + 'px';
                img.parentNode.insertBefore(placeholder, img);
                
                img.style.opacity = '0';
                img.style.transition = 'opacity 0.3s ease-in';
                
                img.addEventListener('load', () => {
                    img.style.opacity = '1';
                    placeholder.remove();
                });
                
                img.addEventListener('error', () => {
                    placeholder.remove();
                });
            });
        }
        
        // 优化触摸事件
        document.addEventListener('touchstart', () => {}, {passive: true});
        
        // 记录性能指标
        performance.mark('end');
        performance.measure('页面加载', 'start', 'end');
        
        // 页面卸载前发送性能数据
        window.addEventListener('unload', () => {
            monitor.sendMetrics();
        });
    });
    </script>
    
    <!-- 添加渐进式加载样式 -->
    <style>
    .media-left img {
        opacity: 0;
        transition: opacity 0.3s ease-in;
    }
    .media-left img.loaded {
        opacity: 1;
    }
    </style>
</head>
<body>
<!-- 性能监控数据 -->
<div id="performance-metrics" style="display: none;">
    <script>
        window.performanceMetrics = {
            cacheHitRate: ''' + str(cache_hit_rate) + ''',
            avgResponseTime: ''' + str(avg_response_time) + ''',
            totalApiCalls: ''' + str(performance_metrics['api_calls']) + ''',
            totalErrors: ''' + str(performance_metrics['errors']) + '''
        };
    </script>
</div>
<center>
'''
    feedback += '''
<center>
<nav>
    <a role="button" class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="navbarUp">
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
    </a>
  </div>

  <div id="navbarUp" class="navbar-menu">
    <div class="navbar-brand">
      <a class="navbar-item" href="https://sj.无名氏.top">
        <figure class="image is-48x48 image is-1by1">
          <img src="https://jiashu.jsdmirror.com/gh/StudioJade/web/logo.webp" width="32" height="32">
        </figure>
        <h3 class="title is-3">StudioJade</h3>
      </a>
    <div class="navbar-start">
      <a class="navbar-item" href="https://github.com/StudioJade/">
        Github
      </a>

      <a class="navbar-item" href="https://40code.com/#page=studio&id=691">
        40code
      </a>

      <div class="navbar-item has-dropdown is-hoverable">
        <a class="navbar-link">
          更多
        </a>

        <div class="navbar-dropdown">
          <a class="navbar-item" href="https://github.com/StudioJade/web/issues/new">
            反馈此网站的bug
          </a>
          <a class="navbar-item" href="https://github.com/StudioJade/web">
            本页面的Github
          </a>
          <a class="navbar-item" href="https://github.com/orgs/StudioJade/repositories">
            开源存储库
          </a>
          <a class="navbar-item" href="https://github.com/wumingshiali">
            室长Github
          </a>
          <a class="navbar-item" href="https://40code.com/#page=user&id=2594">
            室长40code
          </a>
          <a class="navbar-item" href="https://无名氏.top/">
            室长个人网站
          </a>
          <a class="navbar-item" href="https://bulma.org.cn/">
            使用的CSS
          </a>
          <a class="navbar-item" href="./contributors">
            贡献者
          </a>
        </div>
      </div>
    </div>
  </div>
</nav>
'''

    created_date = dt.date(2024, 2, 16)
    today = dt.date.today()
    delta = today - created_date
    
    feedback += f'''
<section class="section">
    <h5 class="subtitle is-5">工作室简介</h5>
    <p>本工作室创建于2024/02/16，距今已有 {delta.days} 天</p>
</section>
<section class="section">
    <h5 class="subtitle is-5">StudioJade成员</h5>
    <div class="container">
        <div class="columns is-multiline is-mobile">'''

    for i in range(len(members_list)):
        profile_url = f'https://40code.com/#page=user&id={id_list[i]}'
        user_image = get_img_code(str(heads_list[i]))
        feedback += f'''
            <div class="column is-narrow">
                <div class="box">
                    <a href="{profile_url}">
                        {user_image}
                        <small>{members_list[i]}</small>
                    </a>
                </div>
            </div>'''

    feedback += '''
        </div>
    </div>
</section>
</center>
</body>
</html>'''
    return feedback

@app.route('/')
def home():
    """主页路由，带缓存控制"""
    members_list, heads_list, id_list = get_members_data()
    response = make_response(generate_html(members_list, heads_list, id_list))
    response.headers['Cache-Control'] = 'public, max-age=300'  # 浏览器缓存5分钟
    return response

if __name__ == '__main__':
    app.run(debug=True)
