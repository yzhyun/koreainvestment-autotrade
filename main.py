import datetime

import KoreaInvestmentApi as kis
from common import *
import time

with open('stock_code.yaml', encoding='UTF-8') as f:
    _code = yaml.load(f, Loader=yaml.FullLoader)

# 자동매매 시작
try:

    kis.ACCESS_TOKEN = kis.get_access_token()

    # 삼성전자: 005930 카카오: 035720 하이닉스: 000660 세틀뱅크: 234340 현대차: 005380
    symbol_list = ["005930", "035720", "000660", "005380"] # 매수 희망 종목 리스트
    bought_list = [] # 매수 완료된 종목 리스트
    standard_price_stock = 100000  # 매매 기준으로 잡은 1주당 금액 ex)1주가 10만원이 넘을 경우
    total_cash = kis.get_balance() # 보유 현금 조회
    stock_dict = kis.get_stock_balance() # 보유 주식 조회
    soldout = False
    REPORT_STOCK_PRICE = False # 프로그램 실행 시 주식 정보 레포트
    dict_stock_info = {} # 매수 희망 종목 정보

    while True:
        t_now = datetime.datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
        t_sell = t_now.replace(hour=15, minute=15, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=20, second=0,microsecond=0)
        today = datetime.datetime.today().weekday()
        if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
            send_message("주말이므로 프로그램을 종료합니다.")
            break
        if t_9 < t_now < t_start and soldout == False:  # 잔여 수량 매도
            for sym, qty in stock_dict.items():
                kis.sell(sym, qty)
                bought_list = []
        if t_start < t_now:
            print("===대상 종목 전일 종가 조회")
            # 대상 종목 전일 종가 및 금일 시가 Report 프로그램 실행 최초 1회 수행

            if not REPORT_STOCK_PRICE:
                for code in symbol_list:
                    print(f"{_code[code]}[{code}]")
                    arr = []
                    res = kis.get_stock_price(code)
                    stck_oprc = int(res.json()['output'][0]['stck_oprc'])  # 오늘 시가
                    stck_hgpr = int(res.json()['output'][1]['stck_hgpr'])  # 전일 고가
                    stck_lwpr = int(res.json()['output'][1]['stck_lwpr'])  # 전일 저가
                    stck_clpr = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가

                    # 0 : 종가의 2% 상승 시 목표가
                    target_price = int(get_target_price(0, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr))

                    arr.append(stck_oprc)
                    arr.append(stck_hgpr)
                    arr.append(stck_lwpr)
                    arr.append(stck_clpr)
                    arr.append(target_price)

                    print(f"오늘 시가: {stck_lwpr}")
                    print(f"전일 고가: {stck_hgpr}")
                    print(f"전일 저가: {stck_lwpr}")
                    print(f"전일 종가: {stck_clpr}")
                    print(f"목표가: {stck_clpr}")
                    msg = _code[code] + "[" + code + "]" + "\n" + "오늘 시가: " + str(stck_lwpr) + "\n" + "전일 종가: " + str(stck_clpr) + "\n" + "목표가: " + str(target_price)
                    send_message(msg)
                    dict_stock_info[code] = arr
                REPORT_STOCK_PRICE = True
            print(dict_stock_info)
            send_message("보유현금: " + str(total_cash))
        if t_start < t_now < t_sell:    # AM 09:05 ~ PM 03:15 : 매수
            # 목표가 도달한 종목에 대해 매수 실행
            for code in dict_stock_info:
                arrTmp = dict_stock_info[code]
                current_price = kis.get_current_price(code)
                buy_qty = 0
                # 목표가보다 현재가가 높은 경우 매수 진행
                if arrTmp[4] < current_price:
                    target_buy_count = current_price // standard_price_stock
                    if target_buy_count == 0:
                        buy_qty = 1
                    else:
                        buy_qty = target_buy_count
                    send_message(f"{_code[code]} 목표가 달성({arrTmp[4]} < {current_price}) 매수를 시도합니다.")
                    res = kis.buy(code, buy_qty)
                    if res.json()['rt_cd'] == '0':
                        bought_list.append(code)
                        soldout = False
                        send_message(f"[매수 성공]{str(res.json())}")
                    else:
                        send_message(f"[매수 실패]{str(res.json())}")
                time.sleep(1)
            # 매수한 종목이 전일 종가 대비 5% 이상이면 욕심부리지 말고 팔자. 미반영 
            time.sleep(1)
        if t_sell < t_now < t_exit:  # PM 03:15 ~ PM 03:20 : 일괄 매도
            if not soldout:
                stock_dict = kis.get_stock_balance()
                for sym, qty in stock_dict.items():
                    kis.sell(sym, qty)
                soldout = True
                bought_list = []
                time.sleep(1)
        if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
            diff_cash = kis.get_balance() - total_cash
            send_message("금일 수익: " + str(diff_cash))
            break
except Exception as e:
    kis.send_message(f"[오류 발생]{e}")
    time.sleep(1)