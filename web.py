import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request
from datetime import datetime
import random

# 1. Firebase 初始化
if os.path.exists('serviceAccountKey.json'):
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()

app = Flask(__name__)

# --- 2. 路由設定 ---

@app.route("/")
def index():
    link = "<h1>歡迎來到張煊佩的網站!</h1>"  
    link += "<a href=/mis>課程</a><hr>"      
    link += "<a href=/today>今天日期</a><hr>"  
    link += "<a href=/about>關於煊佩</a><hr>" 
    link += "<a href=/welcome?u=煊佩&dep=靜宜資管>GET傳值</a><hr>"
    link += "<a href=/account>POST傳值(帳號密碼)</a><hr>"
    link += "<a href=/app>數學運算</a><hr>"
    link += "<a href=/cup>擲茭</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    
    # 老師查詢表單
    link += "<a href=/search>查詢老師及其研究室</a><hr>"
    return link  

@app.route("/search")
def search():
    keyword = request.args.get("kw")
    
    # 這裡放一個簡單的搜尋表單，讓頁面隨時都有輸入框可以搜尋
    search_form = """
        <form action="/search" method="get">
            <input type="text" name="kw" placeholder="輸入老師姓名">
            <button type="submit">搜尋</button>
        </form>
        <hr>
    """

    if not keyword:
        return f"{search_form}請輸入關鍵字<br><a href=/>回到首頁</a>"

    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.get()
    
    # 把表單放在最上面
    result = search_form
    result += f"<h3>關於「{keyword}」的查詢結果：</h3>"
    
    found = False
    for doc in docs:
        user = doc.to_dict()
        if keyword in user.get('name', ''):
            found = True
            result += f"{user['name']}老師的研究室是在 {user['lab']}<br>"
    
    if not found:
        result += "找不到這位老師"
        
    result += "<br><a href=/>回到首頁</a>"
    return result

@app.route("/read")
def read():
    collection_ref = db.collection("靜宜資管")
    # 根據 mail 排序取 3 筆
    docs = collection_ref.order_by("mail", direction=firestore.Query.DESCENDING).limit(3).get()
    
    Temp = "<h3>資料庫前三筆資料：</h3>"
    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"
    return Temp + "<br><a href=/>回到首頁</a>"

# --- 這裡往下是其他功能，確保不要有重複的 read ---

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回到網站首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    date_str = f"{now.year}年{now.month}月{now.day}日"
    return render_template("today.html", datetime=date_str)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name=x, dep=y)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        return f"您輸入的帳號是：{user}；密碼為：{pwd}"
    return render_template("account.html")

@app.route("/app", methods=["GET", "POST"])
def calculate():
    result = None
    if request.method == "POST":
        try:
            x = float(request.form.get("x"))
            y = float(request.form.get("y"))
            opt = request.form.get("opt")
            if opt == "/" and y == 0:
                result = "除數不能為0！"
            else:
                res = 0
                if opt == "+": res = x + y
                elif opt == "-": res = x - y
                elif opt == "*": res = x * y
                elif opt == "/": res = x / y
                result = int(res)
        except Exception:
            result = "輸入格式錯誤"
    return render_template("calculator.html", result=result)

@app.route('/cup', methods=["GET"])
def cup():
    action = request.values.get("action")
    result = None
    if action == 'toss':
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
        result = {"cup1": "/static/" + str(x1) + ".jpg", "cup2": "/static/" + str(x2) + ".jpg", "message": msg}
    return render_template('cup.html', result=result)

if __name__ == "__main__":
    app.run(debug=True)