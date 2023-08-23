import yaml
import requests

with open('security.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

SLACK_WEBHOOK_URL = _cfg['SLACK_WEBHOOK_URL']
SLACK_TOKEN = _cfg['SLACK_TOKEN']
SLACK_CHANNEL = _cfg['SLACK_CHANNEL']

def send_message(msg):
    """slack 메세지 전송"""
    token = SLACK_TOKEN
    channel = SLACK_CHANNEL
    print("slack msg: " + msg)
    res = requests.post(SLACK_WEBHOOK_URL,
                  headers={"Authorization": "Bearer " + token},
                  data={"channel": channel, "text": msg})
    print(res.json())
