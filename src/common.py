import yaml
import requests
import datetime
import time
from logger import *

with open('././config/security.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

SLACK_WEBHOOK_URL = _cfg['SLACK_WEBHOOK_URL']
SLACK_TOKEN = _cfg['SLACK_TOKEN']
SLACK_CHANNEL = _cfg['SLACK_CHANNEL']

logger = log()

STANDARD_PRICE_STOCK = 300000  # 매매 기준으로 잡은 1주당 금액 ex)1주가 10만원이 넘을 경우
SELL_PER = 0.02  # 매도 목표 퍼센트
BUY_PER = 0.01  # 매수 목표 퍼센트
STOP_LOSS_PER = 0.03 # 손절 목표 퍼센트
# BUY_PER = 0  # 매수 목표 퍼센트
MAX_STOCK_NUM = 4


def send_message(msg):
    """slack 메세지 전송"""
    token = SLACK_TOKEN
    channel = SLACK_CHANNEL
    print("slack msg: " + "\n" + msg)
    msg = msg + "\n" + "==============================" + "\n"
    res = requests.post(SLACK_WEBHOOK_URL,
                        headers={"Authorization": "Bearer " + token},
                        data={"channel": channel, "text": msg})
    print(res.json())


def write_report(memo):
    today = datetime.date.today()
    curTime = datetime.datetime.now()
    filepath = 'report/' + str(today)
    f = open(filepath + ".txt", 'a', encoding='UTF-8')
    f.write(f"[{curTime}] {memo} \n")
    f.close()

def write_profit_amt(amt):
    today = datetime.date.today()
    filepath = 'report/profit_' + str(today)
    f = open(filepath + ".txt", 'a', encoding='UTF-8')
    f.write(f" {amt}")
    f.close()

def write_monthly_report(amt):
    today = datetime.date.today()
    filepath = 'report/monthly/' + str(today.year) +  str(today.month)
    f = open(filepath + ".txt", 'a', encoding='UTF-8')
    f.write(f"{str(today.day)} {amt}\n")
    f.close()

def get_target_price(num, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr):
    val = ""
    if num == 0:    # 매수 목표가
        val = stck_oprc * (1 + BUY_PER)  # 금일 시가 1%
        # val = stck_oprc
    elif num == 1:  # 손절 매매가
        val = stck_oprc * (1 - STOP_LOSS_PER) # 금일 시가의 3% 하락 시 매매 (손절)
    return val
