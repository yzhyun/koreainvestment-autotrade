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
symbol_list = ["234340", "000660", "035720", "036800", "066570", "032640", "000880", "005380", "286940", "079160", "069960",
               "004990", "004690", "003490", "035420", "454910"]  # 매수 희망 종목 리스트

logger.info("======================Start the program. Let's be rich======================")
send_message("===Start the program. Let's be rich===")
# KIS 초기화
init_investment()

# 보유 현금 조회
total_cash = get_balance_cash()

wish_stock_dict = {}  # 매수 희망 종목 정보
dict_bought_list = {}  # 매수 완료 정보

# wish_stock_dict = init_trgt_stock_list(symbol_list)
# report_cur_stock_info(dict_bought_list, wish_stock_dict)

isReportTime = False
isInit = True

def set_report_time():
    global isReportTime
    isReportTime = True


# 스케쥴러 초기화
# schedule.every(1).hour.do(reportCurStockInfo, dict_bought_list, wish_stock_dict) # 매시각 보고
schedule.every(30).minutes.do(set_report_time)  # 30분마다 보고
# schedule.every(5).seconds.do(setReportTime)  # 30분마다 보고
# schedule.run_pending()  # 정시에 현재 보유 주식 정보를 보고받고자 스케쥴러 실행

while True:
    try:

        if isReportTime:  # 스케쥴러로 정해진 시간에 중간 보유 주식 보고
            report_cur_stock_info(dict_bought_list, wish_stock_dict)
            isReportTime = False

        t_now = datetime.datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)
        t_start = t_now.replace(hour=9, minute=2, second=0, microsecond=0)
        t_buy = t_now.replace(hour=10, minute=30, second=0, microsecond=0)
        t_sell = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=25, second=0, microsecond=0)

        today = datetime.datetime.today().weekday()

        # if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
        #     send_message("주말이므로 프로그램을 종료합니다.")
        #     break
        # if t_9 <= t_now <= t_start:

        if t_start <= t_now:
            time.sleep(10)  # 시가 조회 시간 여유 부여
            if isInit:  # 첫 1회 초기화
                wish_stock_dict = init_trgt_stock_list(symbol_list)
                report_cur_stock_info(dict_bought_list, wish_stock_dict)
                isInit = False
            schedule.run_pending()  # 정시에 현재 보유 주식 정보를 보고받고자 스케쥴러 실행
        if t_start <= t_now <= t_buy:  # 09:00 ~ 10:30 까지만 매수
            print("=====매수목표가 달성 시 매수 진행")
            print(len(wish_stock_dict))
            # 매수 종목 7개인 경우, 매수 활동 중지
            if len(dict_bought_list) == 7:
                continue
            for code in list(wish_stock_dict.keys()):
                arrTmp = wish_stock_dict[code]
                if code in dict_bought_list:
                    logger.info(f"{_code[code]}=====이미 매수한 종목 입니다.")
                    continue

                # 종목 현재가 조회
                current_price = get_stock_cur_price(code)
                logger.info(f"{_code[code]} 현재가 [{current_price}] / 매수목표가 [{arrTmp[4]}]")

                buy_qty = 0
                # 목표가보다 현재가가 높은 경우 매수 진행
                if arrTmp[4] <= current_price:  # <= int(arrTmp[5] * 1.05):        # 급등 항목은 제외 될 수 있도록
                    # target_buy_count = current_price // standard_price_stock      # 1주당 금액 기준으로 매수 수량 선택
                    target_buy_count = STANDARD_PRICE_STOCK // current_price
                    if target_buy_count == 0:
                        buy_qty = 1
                    else:
                        buy_qty = target_buy_count
                    try:
                        send_message(f"{_code[code]} 목표가 달성({arrTmp[4]} <= {current_price}) 매수를 시도합니다.")
                        if buy_stock(code, buy_qty):
                            dict_bought_list[code] = buy_qty
                            tmp_sell_target_price = wish_stock_dict[code][5]
                            wish_stock_dict[code][5] = int(current_price * (1 + SELL_PER))  # 매수 금액으로 매도 목표 금액 재설정 (2%)
                            send_message(f"[매수 성공]: {_code[code]}({buy_qty})")
                            write_report(f"[매수 성공]: {_code[code]}({buy_qty})")
                            # f"매도 목표가 변경 {tmp_sell_target_price} -> {wish_stock_dict[code][5]}")
                        else:
                            logger.info(f"[매수 실패]: {_code[code]}({buy_qty})")
                            send_message(f"[매수 실패]: {_code[code]}({buy_qty})")
                    except Exception as e:
                        logger.error(f"[매수 오류 발생]{e}")
        if t_buy <= t_now <= t_sell:  # 11:00 ~ 15:20 까지 매도 진행
            # 매수한 종목이 금일 매수금액 대비 2% 이상이면 욕심부리지 말고 팔자. 미반영
            print("=====매도목표가 달성 시 매도 진행")
            if isReportTime:
                time.sleep(2)
            dict_cur_amt = get_my_stock_cur_amt(wish_stock_dict)  # 매수 종목 현재가 가져오기
            time.sleep(1)
            if len(dict_cur_amt) == 0:
                continue  # 보유 주식 없는 경우 PASS

            for code in list(wish_stock_dict.keys()):
                if code in dict_bought_list:
                    arrTmp = wish_stock_dict[code]
                    current_price = dict_cur_amt[code]
                    # time.sleep(1)
                    logger.info(f"{_code[code]} 현재가 [{current_price}] / 매도목표가 [{arrTmp[5]}]")
                    if int(arrTmp[5]) <= int(current_price):
                        send_message(f"{_code[code]} 목표가 달성({arrTmp[4]} <= {current_price}) 매도를 시도합니다.")
                        if code in symbol_list:
                            try:
                                if sell_stock(code, dict_bought_list[code]):
                                    send_message(f"[매도 성공]: {_code[code]}({dict_bought_list[code]})")
                                    del dict_bought_list[code]
                                    del wish_stock_dict[code]
                            except Exception as e:
                                logger.error(f"[매도 오류 발생]{e}")
                # time.sleep(1)
        if t_sell < t_now:  # PM 03:20 ~ PM 03:25 : 일괄 매도
            if len(dict_bought_list) > 0:
                # 잔여 수량 매도
                for code in list(wish_stock_dict.keys()):
                    if code in dict_bought_list:
                        arrTmp = wish_stock_dict[code]
                        if code in symbol_list:
                            try:
                                if sell_stock(code, dict_bought_list[code]):
                                    send_message(f"[매도 성공]: {_code[code]}({dict_bought_list[code]})")
                                    del dict_bought_list[code]
                                    del wish_stock_dict[code]
                                    time.sleep(0.5)
                            except Exception as e:
                                logger.error(f"[매도 오류 발생]{e}")
        if t_exit < t_now:  # PM 03:20 ~ :프로그램 종료
            report_cur_stock_info(dict_bought_list, wish_stock_dict)
            diff_cash = get_balance_cash() - total_cash
            send_message(f"금일 수익: {diff_cash}")
            write_report(f"금일 수익: {diff_cash}")
            break

    except Exception as e:
        logger.error(e.args)
        send_message(f"[오류 발생]{e}")
