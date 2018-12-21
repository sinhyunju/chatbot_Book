# -*- coding: utf-8 -*-
import json
from elice_utils import EliceUtils
import urllib.request
from bs4 import BeautifulSoup

from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

elice_utils = EliceUtils()

slack_token = " your token input "
slack_client_id = " your client_id input"
slack_client_secret = " your client_secret input "
slack_verification = " your verification input "
sc = SlackClient(slack_token)


@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})


    if "event" in slack_event and slack_event["event"]["type"] == "app_mention":


        if "바나나야 카테고리 보여줘" in slack_event["event"]["text"]:
            url = "https://book.naver.com/bestsell/bestseller_list.nhn"
            soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

            category = []

            comments = ""

            i = 1
            for data in soup.find("div", class_="fold_wrap").find("ul").find_all("li"):
                category.append(str(i) + "." + data.get_text().replace("\n", ""))
                i = i + 1

            for k in category:
                comments = comments + k + "\n"

            send_text = "책봇 카테고리 입니당" + "\n" + comments + "\n"
            sc.api_call(
                "chat.postMessage",
                channel=slack_event["event"]["channel"],
                text=send_text
            )

            return make_response("App mention message has been sent", 200, )

        elif "1번 보여줘" in slack_event["event"]["text"]:

            url = "https://book.naver.com/bestsell/bestseller_list.nhn?cp=yes24&cate=total&bestWeek=2018-12-3&indexCount=1&type=list"

            # URL 주소에 있는 HTML 코드를 soup에 저장합니다.
            soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

            teamRank = []
            artist = []
            star=[]
            rivlist = []
            price=[]
            link=[]
            i = 1
            comments = ""

            for data in soup.find_all("a", class_="N=a:bel.title"):
                teamRank.append(str(i) + "위 " + data.get_text())
                i += 1

            for data in soup.find_all("a", class_="txt_name N=a:bel.author"):
                artist.append(data.get_text())

            for data in soup.find_all("dd", class_= "txt_desc"):
                star.append(data.get_text().replace("\r" , "").replace("\t" , "").replace("\n",""))

            for data in star:
                data = data[2:5]
                rivlist.append(data)

            for data in soup.find_all("em", class_ = "price"):
                price.append(data.get_text())

            for i in range(0, 10):
                comments = comments + teamRank[i] + " / " + artist[i]  +  " 평점 : " + rivlist[i] + " 점 "  + " 가격 :" + price[i] + "\n"


            send_text = comments
            sc.api_call(
                "chat.postMessage",
                channel=slack_event["event"]["channel"],
                text=send_text
            )

            return make_response("App mention message has been sent", 200, )

        elif "2번 보여줘" in slack_event["event"]["text"]:

            url = "https://book.naver.com/bestsell/bestseller_list.nhn?cp=yes24&cate=001001044&bestWeek=2018-12-3&indexCount=2&type=list"

            # URL 주소에 있는 HTML 코드를 soup에 저장합니다.
            soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

            teamRank = []
            artist = []
            star=[]
            rivlist = []
            price=[]
            link=[]
            i = 1
            comments = ""

            for data in soup.find_all("a", class_="N=a:bel.title"):
                teamRank.append(str(i) + "위 " + data.get_text())
                i += 1

            for data in soup.find_all("a", class_="txt_name N=a:bel.author"):
                artist.append(data.get_text())

            for data in soup.find_all("dd", class_= "txt_desc"):
                star.append(data.get_text().replace("\r" , "").replace("\t" , "").replace("\n",""))

            for data in star:
                data = data[2:5]
                rivlist.append(data)

            for data in soup.find_all("em", class_ = "price"):
                price.append(data.get_text())

            for i in range(0, 10):
                comments = comments + teamRank[i] + " / " + artist[i]  +  " 평점 : " + rivlist[i] + " 점 "  + " 가격 :" + price[i] + "\n"


            send_text = comments
            sc.api_call(
                "chat.postMessage",
                channel=slack_event["event"]["channel"],
                text=send_text
            )

            return make_response("App mention message has been sent", 200, )

        elif "3번 보여줘" in slack_event["event"]["text"]:

            url = "https://book.naver.com/bestsell/bestseller_list.nhn?cp=yes24&cate=001001045&bestWeek=2018-12-3&indexCount=3&type=list"

            # URL 주소에 있는 HTML 코드를 soup에 저장합니다.
            soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

            teamRank = []
            artist = []
            star=[]
            rivlist = []
            price=[]
            link=[]
            i = 1
            comments = ""

            for data in soup.find_all("a", class_="N=a:bel.title"):
                teamRank.append(str(i) + "위 " + data.get_text())
                i += 1

            for data in soup.find_all("a", class_="txt_name N=a:bel.author"):
                artist.append(data.get_text())

            for data in soup.find_all("dd", class_= "txt_desc"):
                star.append(data.get_text().replace("\r" , "").replace("\t" , "").replace("\n",""))

            for data in star:
                data = data[2:5]
                rivlist.append(data)

            for data in soup.find_all("em", class_ = "price"):
                price.append(data.get_text())

            for i in range(0, 10):
                comments = comments + teamRank[i] + " / " + artist[i]  +  " 평점 : " + rivlist[i] + " 점 "  + " 가격 :" + price[i] + "\n"


            send_text = comments
            sc.api_call(
                "chat.postMessage",
                channel=slack_event["event"]["channel"],
                text=send_text
            )

            return make_response("App mention message has been sent", 200, )

    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)