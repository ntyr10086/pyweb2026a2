from flask import Flask, render_template, request
from datetime import datetime
import random

app = Flask(__name__)

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
    return link                           

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
                # 先把 res 算出來
                res = 0
                if opt == "+": res = x + y
                elif opt == "-": res = x - y
                elif opt == "*": res = x * y
                elif opt == "/": res = x / y
                
                # 算完才轉整數
                result = int(res)
        except Exception:
            result = "輸入格式錯誤"
            
    return render_template("calculator.html", result=result)

@app.route('/cup', methods=["GET"])
def cup():
    # 檢查網址是否有 ?action=toss
    #action = request.args.get('action')
    action = request.values.get("action")
    result = None
    
    if action == 'toss':
        # 0 代表陽面，1 代表陰面
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)
        
        # 判斷結果文字
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
            
        result = {
            "cup1": "/static/" + str(x1) + ".jpg",
            "cup2": "/static/" + str(x2) + ".jpg",
            "message": msg
        }
        
    return render_template('cup.html', result=result)

app = app

if __name__ == "__main__":
    app.run()
