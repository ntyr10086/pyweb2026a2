import requests
from bs4 import BeautifulSoup


import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request
from datetime import datetime
import random

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
    link += "<a href=/spider1>爬蟲</a><hr>"
    link += "<a href=/spider2>查詢即將上映電影</a><hr>"
    link += "<a href=/movie>讀取開眼電影即將上映影片，寫入Firestore</a><hr>"
    link += "<a href=/movie2>查詢開眼電影即將上映電影</a><hr>"
    link += "<a href=/road>十大肇事路口</a><hr>"
    link += "<a href=/weather>查詢天氣</a><hr>"

    return link  


@app.route("/weather", methods=["GET", "POST"])
def weather():
    # 這裡先定義好查詢框的 HTML，讓頁面隨時都有框框可以輸入
    search_form = """
        <form method="post">
            <p>請輸入欲查詢的縣市：
            <input type="text" name="city" placeholder="例如：臺中市" />
            <button type="submit">查詢天氣</button>
            </p>
        </form>
        <hr>
    """

    if request.method == "POST":
        city = request.form.get("city")
        if not city:
            return search_form + "請輸入縣市名稱！<br><a href='/'>回首頁</a>"
        
        city = city.replace("台", "臺")
        # 記得 API Key 要用你自己的喔！
        token = "rdec-key-123-45678-011121314"
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization={token}&format=JSON&locationName={city}"
        
        try:
            data = requests.get(url).json()
            # 檢查 API 是否有回傳資料
            if not data["records"]["location"]:
                return search_form + f"找不到「{city}」的資料，請確認縣市名稱是否正確<br><a href='/'>回首頁</a>"

            location = data["records"]["location"][0]
            weather_element = location["weatherElement"]
            
            # 抓取第一個時段的天氣狀態與降雨機率
            weather_state = weather_element[0]["time"][0]["parameter"]["parameterName"]
            rain_chance = weather_element[1]["time"][0]["parameter"]["parameterName"]
            
            # 把查詢框放在結果上面，這樣可以連續查詢
            res = search_form
            res += f"<h3>{city} 目前天氣預報</h3>"
            res += f"天氣狀況：{weather_state}<br>"
            res += f" 降雨機率：{rain_chance}%<br>"
            res += "<br><a href='/'>回首頁</a>"
            return res
            
        except Exception as e:
            return search_form + f"發生錯誤：{e}<br><a href='/'>回首頁</a>"

    # GET 請求時（第一次進入頁面）只顯示查詢框
    return search_form + "<a href='/'>回首頁</a>"
       

@app.route("/road")
def road():
    R = ""
    url = "https://newdatacenter.taichung.gov.tw/api/v1/no-auth/resource.download?rid=a1b899c0-511f-4e3d-b22b-814982a97e41"
    Data = requests.get(url)
    #print(Data.text)

    JsonData = json.loads(Data.text)
    for item in JsonData:
        R+=item["路口名稱"]+"，總共發生"+item["總件數"]+"件事故<br>"

    return R

@app.route("/movie")
def movie():
  url = "http://www.atmovies.com.tw/movie/next/"
  Data = requests.get(url)
  Data.encoding = "utf-8"
  sp = BeautifulSoup(Data.text, "html.parser")
  result=sp.select(".filmListAllX li")
  lastUpdate = sp.find("div", class_="smaller09").text[5:]

  for item in result:
    picture = item.find("img").get("src").replace(" ", "")
    title = item.find("div", class_="filmtitle").text
    movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
    hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
    show = item.find("div", class_="runtime").text.replace("上映日期：", "")
    show = show.replace("片長：", "")
    show = show.replace("分", "")
    showDate = show[0:10]
    showLength = show[13:]

    doc = {
        "title": title,
        "picture": picture,
        "hyperlink": hyperlink,
        "showDate": showDate,
        "showLength": showLength,
        "lastUpdate": lastUpdate
      }

    db = firestore.client()
    doc_ref = db.collection("電影").document(movie_id)
    doc_ref.set(doc)    
  return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate 



@app.route("/movie2", methods=["POST", "GET"])
def searchQ():
    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]
        info = f"<h2>您查詢的關鍵字是：{MovieTitle}</h2>"
        db = firestore.client()     
        collection_ref = db.collection("電影")
        docs = collection_ref.order_by("showDate").get()
        
        found = False
        for doc in docs:
            m_data = doc.to_dict()
            if MovieTitle in m_data["title"]: 
                found = True
                info += f"片名：{m_data['title']}<br>" 
                info += f"影片介紹：{m_data['hyperlink']}<br>"
                info += f"片長：{m_data['showLength']} 分鐘<br>" 
                info += f"上映日期：{m_data['showDate']}<br><br>"
        
        if not found:
            info += "找不到相關電影"
            
        return info + "<br><a href='movie2'>回查詢頁面</a>"
    
    else:  
        # 直接在這裡寫 HTML 表單，就不需要 input.html 檔案了！
        return '''
            <form method="post">
                <p>請輸入欲查詢的片名：
                <input type="text" name="MovieTitle" />
                <button type="submit">確定送出</button>
                </p>
            </form>
        '''


@app.route("/spider2")
def spider2():
    R = "<h1>即將上映電影</h1>" 
    url = "https://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")

    for item in result:
        # 1. 抓取連結標籤 <a>
        a_tag = item.find("a")
        # 2. 抓取圖片標籤 <img>
        img_tag = item.find("img")
        
        if a_tag and img_tag:
            name = img_tag.get("alt") # 電影名稱
            # 記得把相對網址補全
            link = "https://www.atmovies.com.tw" + a_tag.get("href")
            
            # 把資訊組合成 HTML 字串
            R += f"<b>電影名稱：</b>{name}<br>"
            R += f"<b>介紹連結：</b><a href='{link}'>{link}</a><br><br>"
            
            # 同時在終端機印出來給你看進度
            print(f"抓到囉：{name}")

    return R # 確定所有東西都加進 R 了，最後才送出！


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
    
    Temp = ""
    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"
    return Temp + "<br><a href=/>回到首頁</a>"


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
