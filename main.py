from flask import Flask
import requests as r
import datetime as dt
import time as t

app = Flask(__name__)

def get_img_code(a):
    """根据用户头像ID生成头像HTML"""
    if a == "None":
        return ''
    else:
        return '''<div class="media-left">
      <figure class="image is-32x32 image is-1by1">''' + '<img class="is-rounded" src="https://abc.520gxx.com/static/internalapi/asset/' + a + '" width="32" height="32">' + '''</figure>'''

def get_members_data():
    """从API获取成员数据"""
    res = r.get("https://api.abc.520gxx.com/studio/user?id=691")
    infos = res.json()
    members_list = []
    heads_list = []
    id_list = []
    for member in infos["data"]:
        members_list.append(member["nickname"])
        heads_list.append(member["head"])
        id_list.append(member["id"])
    return members_list, heads_list, id_list

def generate_html(members_list, heads_list, id_list):
    """生成HTML页面"""
    feedback = '''
<!DOCTYPE html>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>StudioJade网站</title>
<link rel="icon" href="https://cdn.jsdelivr.net/gh/StudioJade/web/logo.png" type="image/x-icon">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma/css/bulma.min.css">
'''
    # 导航栏
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
    y = int(t.strftime("%Y")) - 2024
    m = int(t.strftime("%m")) - 2
    d = int(t.strftime("%d")) - 16
    if d < 0:
        m -= 1
        d += 30
    if m < 0:
        y -= 1
        m += 12
    feedback += '''
<h5 class="subtitle is-5">工作室简介</h5>
工作室flag:宁为玉碎，不为瓦全。<br>
本工作室创建于2024/02/16，距今已有
''' + str(y) + '年' + str(m) + '个月' + str(d) + '天'
    feedback += '''
<h5 class="subtitle is-5">StudioJade成员</h5>'''
    for i in range(len(members_list)):
        # 构建用户个人页面链接
        profile_url = 'https://40code.com/#page=user&id=' + str(id_list[i])
        
        # 获取用户头像HTML
        user_image = get_img_code(str(heads_list[i]))
        
        # 构建单个成员的HTML结构
        member_html = '''<div><div class="box">
        <a href="''' + profile_url + '">' + user_image + '<small>' + members_list[i] + '''</small></div></div></a></div>'''
        
        # 添加到总体反馈中
        feedback += member_html
    feedback += '</center>'
    return feedback

@app.route('/')
def home():
    """主页路由，显示所有成员信息"""
    # 获取信息
    members_list, heads_list, id_list = get_members_data()
    
    # 生成回复
    return generate_html(members_list, heads_list, id_list)
@app.route('/contributors')
def contributors():
    """贡献者路由，显示所有贡献者信息"""
    return '''
<a href="https://github.com/studiojade/web/graphs/contributors">
    <img src="https://contri.buzz/api/wall?repo=studiojade/web&onlyAvatars=true" alt="Contributors' Wall for studiojade/web" />
</a>
'''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3244)