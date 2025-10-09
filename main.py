from flask import Flask
import requests as r

app = Flask(__name__)

def get_img_code(a):
    """根据用户头像ID生成头像HTML"""
    if a == "None":
        return ''
    else:
        return '''<div class="media-left">
      <figure class="image is-32x32 image is-1by1">''' + '<img class="is-rounded" src="https://abc.520gxx.com/static/internalapi/asset/' + a + '" width="32" height="32">' + '''</figure>'''

def color_members(a):
    """根据成员数量返回进度条的颜色类"""
    if a <= 5:
        return 'is-link'
    elif a <= 10:
        return 'is-primary'
    elif a <= 15:
        return 'is-info'
    elif a <= 20:
        return 'is-success'
    elif a <= 25:
        return 'is-warning'
    else:
        return 'is-danger'

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
<title>StudioJade官方网站</title>
<link rel="icon" href="https://cdn.jsdelivr.net/gh/StudioJade/web/logo.png" type="image/x-icon">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma/css/bulma.min.css">
'''
    # 导航栏
    feedback += '''
<nav class="navbar" role="navigation" aria-label="main navigation">
  <div class="navbar-brand">

    <a role="button" class="navbar-burger" aria-label="menu" aria-expanded="false" data-target="navbarBasicExample">
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
      <span aria-hidden="true"></span>
    </a>
  </div>

  <div id="navbarBasicExample" class="navbar-menu">
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
        </div>
      </div>
    </div>
  </div>
</nav>
'''
    feedback += '''<h1 class="title">StudioJade官方网站</h1>
<h2 class="subtitle">StudioJade成员</h2>'''
    for i in range(len(members_list)):
        # 构建用户个人页面链接
        profile_url = 'https://40code.com/#page=user&id=' + str(id_list[i])
        
        # 获取用户头像HTML
        user_image = get_img_code(str(heads_list[i]))
        
        # 构建单个成员的HTML结构
        member_html = '''<div><div class="box">
        <a href="''' + profile_url + '">' + user_image + '<small>' + members_list[i] + '''</small></div></div></a></div>'''
        
        # 添加到总体反馈中
        feedback += member_html + '<br>'
    
    # 添加成员数量进度条
    member_count = len(members_list)
    progress_color = color_members(member_count)
    progress_html = '成员数量<br><progress class="progress ' + progress_color + ' is-warning" value="' + str(member_count) + '" max="50"></progress>'
    feedback += progress_html
    
    return feedback

@app.route('/')
def home():
    """主页路由，显示所有成员信息"""
    # 获取信息
    members_list, heads_list, id_list = get_members_data()
    
    # 生成回复
    return generate_html(members_list, heads_list, id_list)

if __name__ == '__main__':
    app.run(debug=True)