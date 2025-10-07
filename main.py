from flask import Flask
import requests as r

app = Flask(__name__)

def get_img_code(a):
    if a == "None":
        return ''
    else:
        return '<img src="https://abc.520gxx.com/static/internalapi/asset/' + a + '" width="50" height="50">'
@app.route('/')
def home():
    # 获取信息
    res = r.get("https://api.abc.520gxx.com/studio/user?id=691")
    infos = res.json()
    members_list = []
    heads_list = []
    id_list = []
    for member in infos["data"]:
        members_list.append(member["nickname"])
        heads_list.append(member["head"])
        id_list.append(member["id"])
    
    # 生成回复
    feedback = '<!DOCTYPE html>\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bulma@1.0/css/bulma.min.css">\n'
    for i in range(len(members_list)):
        feedback += '<a href="' + 'https://40code.com/#page=user&id=' + str(id_list[i]) + '">' + get_img_code(str(heads_list[i])) + '<p>' + members_list[i] + '</p></a>' + '<br>'

    return feedback

if __name__ == '__main__':
    app.run(debug=True)