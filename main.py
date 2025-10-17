from flask import Flask, make_response, render_template_string
import requests as r
import datetime as dt
from datetime import datetime
import time as t
import os

app = Flask(__name__)

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

def get_img_code(avatar_id, index=0):
    """根据用户头像ID生成头像HTML"""
    # 默认头像的 data URL（一个简单的灰色圆圈SVG）
    default_img = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGNpcmNsZSBjeD0iMTYiIGN5PSIxNiIgcj0iMTYiIGZpbGw9IiNlMGUwZTAiLz48L3N2Zz4="
    
    if avatar_id == "None":
        img_url = default_img
    else:
        img_url = f"https://abc.520gxx.com/static/internalapi/asset/{avatar_id}"
    
    # 根据索引设置加载优先级
    priority = "high" if index < 3 else "low"
    loading = "eager" if index < 3 else "lazy"
    
    return '\n'.join([
        '        <div class="media-left">',
        '            <figure class="image is-32x32 image is-1by1">',
        f'                <img class="is-rounded" loading="{loading}" decoding="async" fetchpriority="{priority}"',
        f'                     src="{img_url}" width="32" height="32" alt="用户头像"',
        f'                     onload="this.classList.add(\'loaded\')" onerror="this.src=\'{default_img}\'">',
        '                <noscript>',
        f'                    <img class="is-rounded" src="{default_img}" width="32" height="32" alt="用户头像">',
        '                </noscript>',
        '            </figure>',
        '        </div>'
    ])

def get_members_data():
    """从API获取成员数据，带简单缓存机制和错误重试"""
    current_time = t.time()
    
    # 检查缓存状态
    cache_age = current_time - cache['timestamp']
    cache_valid = cache['data'] is not None and cache_age < CACHE_DURATION
    cache_stale = cache['data'] is not None and cache_age < (CACHE_DURATION + CACHE_STALE_WHILE_REVALIDATE)
    
    # 如果缓存有效，直接返回
    if cache_valid:
        return cache['data']
    
    # 如果缓存过期但在允许范围内，标记后台刷新
    if cache_stale and not cache['is_revalidating']:
        cache['is_revalidating'] = True
    
    # 获取新数据，添加重试机制
    max_retries = 3
    retry_delay = 1
    last_error = None
    
    for attempt in range(max_retries):
        try:
            session = r.Session()
            session.headers.update({
                'Accept-Encoding': 'gzip, deflate',
                'Cache-Control': 'max-age=0'
            })
            
            res = session.get("https://api.abc.520gxx.com/studio/user?id=691", timeout=5)
            res.raise_for_status()
            infos = res.json()
            
            data = ([m["nickname"] for m in infos["data"]], 
                   [m["head"] for m in infos["data"]], 
                   [m["id"] for m in infos["data"]])
            
            # 更新缓存
            cache['data'] = data
            cache['timestamp'] = current_time
            cache['is_revalidating'] = False
            cache['last_error'] = None
            cache['error_count'] = 0
            
            return data
            
        except Exception as e:
            last_error = e
            cache['error_count'] += 1
            
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
    """生成HTML页面"""
    created_date = dt.date(2024, 2, 16)
    today = dt.date.today()
    delta = today - created_date
    
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="zh-CN">',
        '<head>',
        '    <meta charset="UTF-8">',
        '    <title>StudioJade网站</title>',
        '    <meta name="viewport" content="width=device-width, initial-scale=1">',
        '    <meta name="description" content="StudioJade工作室官方网站">',
        '    <link rel="stylesheet" href="https://s4.zstatic.net/npm/bulma/css/bulma.min.css">',
        '    <style>',
        '        .media-left { display: flex; align-items: center; }',
        '        .is-rounded { border-radius: 50%; }',
        '        img { max-width: 100%; height: auto; }',
        '        .navbar-brand img { object-fit: contain; aspect-ratio: 1; }',
        '        .section { text-align: center; }',
        '        .columns { justify-content: center; }',
        '        .box { text-align: center; }',
        '        @media (max-width: 768px) {',
        '            .navbar-item, button, a {',
        '                min-height: 44px;',
        '                min-width: 44px;',
        '                padding: 12px;',
        '            }',
        '        }',
        '    </style>',
        '</head>',
        '<body>',
        
        # 导航栏
        '    <nav class="navbar" role="navigation" aria-label="main navigation">',
        '        <div class="navbar-brand">',
        '            <a class="navbar-item" href="https://sj.无名氏.top">',
        '                <img src="https://jiashu.jsdmirror.com/gh/StudioJade/web/logo.webp" width="32" height="32">',
        '                <h3 class="title is-3">StudioJade</h3>',
        '            </a>',
        '            <a role="button" class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="navMenu">',
        '                <span aria-hidden="true"></span>',
        '                <span aria-hidden="true"></span>',
        '                <span aria-hidden="true"></span>',
        '            </a>',
        '        </div>',
        '',
        '        <div id="navMenu" class="navbar-menu">',
        '            <div class="navbar-start">',
        '                <a class="navbar-item" href="https://github.com/StudioJade/">Github</a>',
        '                <a class="navbar-item" href="https://40code.com/#page=studio&id=691">40code</a>',
        '                <div class="navbar-item has-dropdown is-hoverable">',
        '                    <a class="navbar-link">更多</a>',
        '                    <div class="navbar-dropdown">',
        '                        <a class="navbar-item" href="https://github.com/StudioJade/web/issues/new">反馈此网站的bug</a>',
        '                        <a class="navbar-item" href="https://github.com/StudioJade/web">本页面的Github</a>',
        '                        <a class="navbar-item" href="https://github.com/orgs/StudioJade/repositories">开源存储库</a>',
        '                        <a class="navbar-item" href="https://github.com/wumingshiali">室长Github</a>',
        '                        <a class="navbar-item" href="https://40code.com/#page=user&id=2594">室长40code</a>',
        '                        <a class="navbar-item" href="https://无名氏.top/">室长个人网站</a>',
        '                        <a class="navbar-item" href="https://bulma.org.cn/">使用的CSS</a>',
        '                        <a class="navbar-item" href="./contributors">贡献者</a>',
        '                    </div>',
        '                </div>',
        '            </div>',
        '        </div>',
        '    </nav>',
        
        # 工作室简介
        '    <section class="section">',
        '        <h5 class="subtitle is-5">工作室简介</h5>',
        f'        <p>本工作室创建于2024/02/16，距今已有 {delta.days} 天</p>',
        '    </section>',
        
        # 成员列表开始
        '    <section class="section">',
        '        <h5 class="subtitle is-5">StudioJade成员</h5>',
        '        <div class="container">',
        '            <div class="columns is-multiline is-mobile">'
    ]
    
    # 生成成员卡片
    for i in range(len(members_list)):
        profile_url = f'https://40code.com/#page=user&id={id_list[i]}'
        user_image = get_img_code(str(heads_list[i]), i)
        html_parts.extend([
            '                <div class="column is-narrow">',
            '                    <div class="box">',
            f'                        <a href="{profile_url}">',
            f'{user_image}',
            f'                            <small>{members_list[i]}</small>',
            '                        </a>',
            '                    </div>',
            '                </div>'
        ])
    
    # 页面结尾
    html_parts.extend([
        '            </div>',
        '        </div>',
        '    </section>',
        '</body>',
        '</html>'
    ])
    
    return '\n'.join(html_parts)

@app.route('/')
def home():
    """主页路由，带缓存控制"""
    members_list, heads_list, id_list = get_members_data()
    response = make_response(generate_html(members_list, heads_list, id_list))
    response.headers['Cache-Control'] = 'public, max-age=300'  # 浏览器缓存5分钟
    return response

if __name__ == '__main__':
    app.run(debug=True)