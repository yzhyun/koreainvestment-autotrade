import sys, os
import datetime, schedule
import KoreaInvestmentApi as kis
from investmentApi import *
from common import *
import time

with open('./config/stock_code.yaml', encoding='UTF-8') as f:
    _code = yaml.load(f, Loader=yaml.FullLoader)

# 삼성전자: 005930 카카오: 035720 하이닉스: 000660 세틀뱅크: 234340 현대차: 005380 나이스정보통신: 036800 LG전자: 066570 LG유플러스: 032640
# 한화: 000880 롯데정보통신: 286940 CJ CGV: 079160 롯데지주: 004990 삼천리: 004690 대한항공: 003490 네이버: 035420 두산로보티스: 454910
symbol_list = ["234340", "000660", "005380", "035720", "036800", "066570", "032640", "000880",
               "286940", "079160", "069960", "004990", "004990", "004690", "003490", "035420",
               "454910"]  # 매수 희망 종목 리스트

SET_INIT = True

logger.info("======================Start the program. Let's be rich======================")
# KIS 초기화
initInvestement()

# 보유 현금 조회
total_cash = getBalanceCash()
print(total_cash)

wish_stock_dict = {}   # 매수 희망 종목 정보
dict_bought_list = {}  # 매수 완료 정보

# 스케쥴러 초기화
#schedule.every(1).hour.do(reportCurStockInfo, dict_bought_list, wish_stock_dict) # 매시각 보고
schedule.every(2).seconds.do(reportCurStockInfo, dict_bought_list, wish_stock_dict) # 매시각 보고

while True:
    try:
        schedule.run_pending()  # 정시에 현재 보유 주식 정보를 보고받고자 스케쥴러 실행

        t_now = datetime.datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=5, second=0, microsecond=0)
        t_sell = t_now.replace(hour=15, minute=0, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
        today = datetime.datetime.today().weekday()

        # if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
        #     send_message("주말이므로 프로그램을 종료합니다.")
        #     break
        if t_9 <= t_now <= t_start:
            if SET_INIT:
                # 잔여 수량 매도
                # stock_dict = getBalanceStock()  # 보유 주식 조회
                # res = sellAllStocks(stock_dict, symbol_list)
                # if res["rtnCd"] != "S":
                #     msg = ""
                #     for code in res["failCodes"]:
                #         msg += f"{_code[code]}/"
                #     send_message(f"[매도 실패]: {msg}")

                # 대상 종목 초기화
                wish_stock_dict = initTrgtStockList(symbol_list)
                send_message("보유현금: " + str(total_cash))
            SET_INIT = False

        if not SET_INIT and (t_9 <= t_now <= t_sell):  # Report 완료 후 수행, 15시까지만 매수
            print("=====매수목표가 달성 시 매수 진행")
            for code in list(wish_stock_dict.keys()):
                arrTmp = wish_stock_dict[code]
                current_price = getStockCurPrice(code)
                time.sleep(0.5)
                logger.info(f"{_code[code]} 현재가 [{current_price}] / 매수목표가 [{arrTmp[4]}]")
                if code in dict_bought_list:
                    logger.info("=====이미 매수한 종목 입니다.")
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
                        if(buyStock(code, buy_qty)):
                            dict_bought_list[code] = buy_qty
                            tmp_sell_target_price = wish_stock_dict[code][5]
                            wish_stock_dict[code][5] = int(current_price * 1.02)  # 매수 금액으로 매도 목표 금액 재설정
                            send_message(f"[매수 성공]: {_code[code]}({buy_qty})")
                            write_report(f"[매수 성공]: {_code[code]}({buy_qty})")
                            # f"매도 목표가 변경 {tmp_sell_target_price} -> {wish_stock_dict[code][5]}")
                        else:
                            logger.info("매수실패 ")
                            send_message(f"[매수 실패]")
                    except Exception as e :
                        logger.error(f"[매수 오류 발생]{e}")

            # 매수한 종목이 금일 매수금액 대비 2% 이상이면 욕심부리지 말고 팔자. 미반영
            print("=====매도목표가 달성 시 매도 진행")
            for code in list(wish_stock_dict.keys()):
                arrTmp = wish_stock_dict[code]
                current_price = getStockCurPrice(code)
                time.sleep(0.5)
                logger.info(f"{_code[code]} 현재가 [{current_price}] / 매도목표가 [{arrTmp[5]}]")
                if int(arrTmp[5]) <= int(current_price):
                    send_message(f"{_code[code]} 목표가 달성({arrTmp[4]} <= {current_price}) 매도를 시도합니다.")
                    if code in symbol_list:
                        try:
                            if kis.sell(code, dict_bought_list[code]):
                                send_message(f"[매도 성공]: {_code[code]}({dict_bought_list[code]})")
                                del dict_bought_list[code]
                                del wish_stock_dict[code]
                        except Exception as e:
                            logger.error(f"[매도 오류 발생]{e}")
                        time.sleep(1)
        if t_sell < t_now < t_exit:  # PM 03:15 ~ PM 03:20 : 일괄 매도
            if len(dict_bought_list) > 0:
                #잔여 수량 매도
                stock_dict = getBalanceStock()  # 보유 주식 조회
                res = sellAllStocks(stock_dict, symbol_list)
                if res["rtnCd"] != "S":
                    msg = ""
                    for code in res["failCodes"]:
                        msg += f"{_code[code]}/"
                    send_message(f"[매도 실패]: {msg}")
            time.sleep(1)
        if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
            print(getBalanceCash())
            diff_cash = getBalanceCash() - total_cash
            send_message(f"금일 수익: {diff_cash}")
            write_report(f"금일 수익: {diff_cash}")
            getRealProfit()
            #break

    except Exception as e:
        logger.error(e.args)
        send_message(f"[오류 발생]{e}")

