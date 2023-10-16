import yaml
import requests

with open('./../config/security.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)


SLACK_WEBHOOK_URL = _cfg['SLACK_WEBHOOK_URL']
SLACK_TOKEN = _cfg['SLACK_TOKEN']
SLACK_CHANNEL = _cfg['SLACK_CHANNEL']

def send_message(msg):
    """slack 메세지 전송"""
    token = SLACK_TOKEN
    channel = SLACK_CHANNEL
    print("slack msg: " +"\n" + msg)
    msg = msg + "\n" + "==============================" + "\n"
    res = requests.post(SLACK_WEBHOOK_URL,
                  headers={"Authorization": "Bearer " + token},
                  data={"channel": channel, "text": msg})
    #print(res.json())

def get_target_price(num, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr):
    val = ""
    if num == 0:
        val = stck_oprc + stck_oprc * 0.02  # 오늘 시가 * 0.02
    elif num == 1:
        val = stck_oprc + (stck_hgpr - stck_lwpr) * 0.5 # 오늘 시가 + (전일 고가 - 전일 저가)/2
    return val




