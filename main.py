from flask import Flask, make_response
import requests as r
import datetime as dt
import time as t
import json

app = Flask(__name__)

# 缓存配置
CACHE_DURATION = 600  # 缓存10分钟
cache = {
    'data': None,
    'timestamp': 0
}

def get_img_code(a):
    """根据用户头像ID生成头像HTML，添加懒加载"""
    if a == "None":
        return '''<div class="media-left">
      <figure class="image is-32x32 image is-1by1">
        <img class="is-rounded" loading="lazy" src="https://abc.520gxx.com/static/internalapi/asset/6e2b0b1056aaa08419fb69a3d7aa5727.png" width="32" height="32">
      </figure>
    </div>'''
    return f'''<div class="media-left">
      <figure class="image is-32x32 image is-1by1">
        <img class="is-rounded" loading="lazy" src="https://abc.520gxx.com/static/internalapi/asset/{a}" width="32" height="32">
      </figure>
    </div>'''

def get_members_data():
    """从API获取成员数据，带缓存机制"""
    current_time = t.time()
    
    # 检查缓存是否有效
    if cache['data'] and current_time - cache['timestamp'] < CACHE_DURATION:
        return cache['data']
    
    # 获取新数据
    try:
        res = r.get("https://api.abc.520gxx.com/studio/user?id=691", timeout=5)
        infos = res.json()
        data = ([m["nickname"] for m in infos["data"]], 
                [m["head"] for m in infos["data"]], 
                [m["id"] for m in infos["data"]])
        
        # 更新缓存
        cache['data'] = data
        cache['timestamp'] = current_time
        return data
    except Exception as e:
        print(f"API请求错误: {e}")
        return [], [], []

def generate_html(members_list, heads_list, id_list):
    """生成优化后的HTML页面"""
    feedback = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="StudioJade工作室官方网站">
    <title>StudioJade网站</title>
    <link rel="icon" href="https://jiashu.jsdmirror.com/gh/StudioJade/web/logo.png" type="image/x-icon">
    <link rel="stylesheet" href="https://s4.zstatic.net/npm/bulma/css/bulma.min.css">
</head>
<body>
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
          <img src="https://cdn.jsdelivr.net/gh/StudioJade/web/logo.png" width="32" height="32">
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
