import yaml
import requests
import datetime
import time
from logger import *

with open('././config/security.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

with open('./config/stock_code.yaml', encoding='UTF-8') as f:
    _code = yaml.load(f, Loader=yaml.FullLoader)

SLACK_WEBHOOK_URL = _cfg['SLACK_WEBHOOK_URL']
SLACK_TOKEN = _cfg['SLACK_TOKEN']
SLACK_CHANNEL = _cfg['SLACK_CHANNEL']

logger = log()

STANDARD_PRICE_STOCK = 300000  # 매매 기준으로 잡은 1주당 금액 ex)1주가 10만원이 넘을 경우
SELL_PER = 0.02 # 매수 목표 퍼센트


def send_message(msg):
    """slack 메세지 전송"""
    token = SLACK_TOKEN
    channel = SLACK_CHANNEL
    print("slack msg: " + "\n" + msg)
    msg = msg + "\n" + "==============================" + "\n"
    res = requests.post(SLACK_WEBHOOK_URL,
                        headers={"Authorization": "Bearer " + token},
                        data={"channel": channel, "text": msg})
    # print(res.json())

def write_report(memo):
    today = datetime.date.today()
    curTime = datetime.datetime.now()
    filepath = 'report/' + str(today)
    f = open(filepath+".txt", 'a')
    f.write(f"[{curTime}] {memo} \n")
    f.close()

def get_target_price(num, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr):
    val = ""
    if num == 0:
        val = stck_clpr * 1.015  # 전일 종가 * 0.02
    elif num == 1:
        val = stck_oprc + (stck_hgpr - stck_lwpr) * 0.5  # 오늘 시가 + (전일 고가 - 전일 저가)
    return val

