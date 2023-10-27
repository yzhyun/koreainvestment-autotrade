import sys, os
import datetime, schedule
import KoreaInvestmentApi as kis

from logger import *
from common import *
import time


with open('./config/stock_code.yaml', encoding='UTF-8') as f:
    _code = yaml.load(f, Loader=yaml.FullLoader)

# 삼성전자: 005930 카카오: 035720 하이닉스: 000660 세틀뱅크: 234340 현대차: 005380 나이스정보통신: 036800 LG전자: 066570 LG유플러스: 032640 한화: 000880 롯데정보통신: 286940 CJ CGV: 079160
# 롯데지주: 004990 삼천리: 004690 대한항공: 003490 네이버: 035420 두산로보티스: 454910
symbol_list = ["234340", "000660", "005380", "035720", "036800", "066570", "032640", "000880",
               "286940", "079160", "069960", "004990", "004990", "004690", "003490", "035420",
               "454910"]  # 매수 희망 종목 리스트

logger = log()  # 로그 설정
STANDARD_PRICE_STOCK = 200000  # 매매 기준으로 잡은 1주당 금액 ex)1주가 10만원이 넘을 경우
SELL_PER = 0.02 # 매수 목표 퍼센트
REPORT_STOCK_PRICE = False  # 프로그램 실행 시 주식 정보 레포트 1회

logger.info("======================Start the program. Let's be rich======================")
# 토큰 생성
kis.ACCESS_TOKEN = kis.get_access_token()
schedule.every(1).hour.do(test) # 매시각 보고

total_cash = kis.get_balance()  # 보유 현금 조회
stock_dict = kis.get_stock_balance()  # 보유 주식 조회

dict_stock_info = {}  # 매수 희망 종목 정보
dict_bought_list = {}  # 매수 완료 정보

while True:
    try:
        schedule.run_pending()  # 정시에 현재 보유 주식 정보를 보고받고자 스케쥴러 실행
        t_now = datetime.datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
        t_sell = t_now.replace(hour=15, minute=0, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
        today = datetime.datetime.today().weekday()

        if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
            send_message("주말이므로 프로그램을 종료합니다.")
            break
        if t_9 < t_now < t_start:  # 잔여 수량 매도
            for code, qty in stock_dict.items():
                if code in symbol_list:  # 매수 희망 종목 리스트에 포함된 주식만 해당 프로그램에서 다룬다.
                    try:
                        if kis.sell(code, qty):
                            send_message(f"[매도 성공]{str(res.json())}")
                        else:
                            send_message(f"[매도 실패]{str(res.json())}")
                    except Exception as e:
                        logger.error(f"[매도 오류 발생]{e}")

            # 대상 종목 전일 종가 및 금일 시가 Report 프로그램 실행 최초 1회 수행
            if not REPORT_STOCK_PRICE:
                logger.info("===대상 종목 전일 종가 조회")
                for code in symbol_list:
                    logger.info(f"{_code[code]}[{code}]")
                    arr = []
                    res = kis.get_stock_price(code)
                    stck_oprc = int(res.json()['output'][0]['stck_oprc'])  # 오늘 시가
                    stck_hgpr = int(res.json()['output'][1]['stck_hgpr'])  # 전일 고가
                    stck_lwpr = int(res.json()['output'][1]['stck_lwpr'])  # 전일 저가
                    stck_clpr = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가

                    # 0 : 종가의 2% 상승 시 목표가
                    target_price = int(get_target_price(0, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr))
                    sell_target_price = int(target_price + target_price * SELL_PER)

                    arr.append(stck_oprc)  # 오늘 시가
                    arr.append(stck_hgpr)  # 전일 고가
                    arr.append(stck_lwpr)  # 전일 저가
                    arr.append(stck_clpr)  # 전일 종가
                    arr.append(target_price)  # 매수 목표가
                    arr.append(sell_target_price)  # 매매 목표가

                    logger.info(f"오늘 시가: {stck_oprc}")
                    logger.info(f"전일 고가: {stck_hgpr}")
                    logger.info(f"전일 저가: {stck_lwpr}")
                    logger.info(f"전일 종가: {stck_clpr}")
                    logger.info(f"매수 목표가:    {target_price}")
                    logger.info(f"매도 목표가:    {sell_target_price}")

                    msg = _code[code] + "[" + code + "]" + "\n" + "오늘 시가: " + str(stck_lwpr) + "\n" + "전일 종가: " \
                          + str(stck_clpr) + "\n" + "매수목표가: " + str(target_price) + "\n" + "매도목표가: " + str(
                        sell_target_price)
                    send_message(msg)
                    dict_stock_info[code] = arr
                REPORT_STOCK_PRICE = True
            # send_message("보유현금: " + str(total_cash))
        if REPORT_STOCK_PRICE and (t_9 < t_now < t_sell):  # Report 완료 후 수행
            print("=====매수목표가 달성 시 매수 진행")
            for code in list(dict_stock_info.keys()):
                arrTmp = dict_stock_info[code]
                current_price = kis.get_current_price(code)
                time.sleep(0.5)
                logger.info(f"{_code[code]} 현재가 [{current_price}] / 매수목표가 [{arrTmp[4]}]")
                if code in dict_bought_list:
                    #logger.info("=====이미 매수한 종목 입니다.")
                    continue
                buy_qty = 0
                # 목표가보다 현재가가 높은 경우 매수 진행
                if arrTmp[4] <= current_price <= int(arrTmp[5] * 1.05): # 급등 항목은 제외 될 수 있도록
                    #target_buy_count = current_price // standard_price_stock    # 1주당 금액 기준으로 매수 수량 선택
                    target_buy_count = STANDARD_PRICE_STOCK // current_price
                    if target_buy_count == 0:
                        buy_qty = 1
                    else:
                        buy_qty = target_buy_count
                    try:
                        send_message(f"{_code[code]} 목표가 달성({arrTmp[4]} <= {current_price}) 매수를 시도합니다.")
                        res = kis.buy(code, buy_qty)
                    except Exception as e :
                        logger.error(f"[매수 오류 발생]{e}")
                    if res.json()['rt_cd'] == '0':
                        dict_bought_list[code] = buy_qty
                        tmp_sell_target_price = dict_stock_info[code][5]
                        dict_stock_info[code][5] = int(current_price * 1.02)  # 매수 금액으로 매도 목표 금액 재설정
                        # del dict_stock_info[code]   # 매수했으므로 매수 희망 종목 리스트에서 제외
                        send_message(f"[매수 성공]: {_code[code]}({buy_qty})")
                        write_report(f"[매수 성공]: {_code[code]}({buy_qty})")
                        # f"매도 목표가 변경 {tmp_sell_target_price} -> {dict_stock_info[code][5]}")
                    else:
                        logger.info("매수실패 ")
                        send_message(f"[매수 실패]")
                    time.sleep(1)

            # 매수한 종목이 금일 매수금액 대비 2% 이상이면 욕심부리지 말고 팔자. 미반영
            print("=====매도목표가 달성 시 매도 진행")
            for code in list(dict_stock_info.keys()):
                arrTmp = dict_stock_info[code]
                current_price = kis.get_current_price(code)
                time.sleep(0.5)
                logger.info(f"{_code[code]} 현재가 [{current_price}] / 매도목표가 [{arrTmp[5]}]")
                if int(arrTmp[5]) <= int(current_price):
                    send_message(f"{_code[code]} 목표가 달성({arrTmp[4]} <= {current_price}) 매도를 시도합니다.")
                    if code in symbol_list:
                        try:
                            if kis.sell(code, dict_bought_list[code]):
                                send_message(f"[매도 성공]: {_code[code]}({dict_bought_list[code]})")
                                del dict_bought_list[code]
                                del dict_stock_info[code]
                        except Exception as e:
                            logger.error(f"[매도 오류 발생]{e}")
                        time.sleep(1)
        if t_sell < t_now < t_exit:  # PM 03:15 ~ PM 03:20 : 일괄 매도
            if len(dict_bought_list) > 0:
                stock_dict = kis.get_stock_balance()
                for code, qty in stock_dict.items():
                    if code in symbol_list:
                        try:
                            if kis.sell(code, dict_bought_list[code]):
                                send_message(f"[매도 성공]: {_code[code]}({dict_bought_list[code]})")
                                del dict_bought_list[code]
                                del dict_stock_info[code]
                        except Exception as e:
                            logger.error(f"[일괄 매도 오류 발생]{e}")
            time.sleep(1)
        # if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
        #     diff_cash = kis.get_balance() - total_cash
        #     send_message(f"금일 수익: {diff_cash}")
        #     write_report(f"금일 수익: {diff_cash}")
        #     break

    except Exception as e:
        logger.error(e)
        kis.send_message(f"[오류 발생]{e}")

