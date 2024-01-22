import sys, os
import datetime, schedule
from investmentApi import *
from common import *
import time
import mysql as db


isReportTime = False    # 중간 보고 용 flag
isInit = True
isSaveProfit = False

send_message("==>Check system")

# KIS, db 초기화
init_investment()

send_message("==>Start the program. Let's be rich")
logger.info("======================Start the program. Let's be rich======================")

# 희망 매수 종목 셋팅
symbol_list = init_symbol_list()

wish_stock_dict = {}  # 매수 희망 종목 정보
dict_bought_list = {}  # 매수 완료 정보

#수수료 수기 업데이트용
#upd_charge_amt("20240119")

def set_report_time():
    global isReportTime
    isReportTime = True

# 스케쥴러 초기화
schedule.every(30).minutes.do(set_report_time)  # 30분마다 보고
while True:
    try:
        if isReportTime:  # 스케쥴러로 정해진 시간에 중간 보유 주식 보고
            report_cur_stock_info(dict_bought_list, wish_stock_dict)
            isReportTime = False

        t_now = datetime.datetime.now()
        t_9 = t_now.replace(hour=9, minute=0, second=0, microsecond=0)

        t_start = t_now.replace(hour=9, minute=1, second=0, microsecond=0)
        t_buy_start = t_now.replace(hour=9, minute=2, second=0, microsecond=0)
        t_buy_end = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
        t_sell_start = t_now.replace(hour=9, minute=31, second=0, microsecond=0)

        t_sell_end = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=30, second=0, microsecond=0)
        t_report = t_now.replace(hour=16, minute=0, second=0, microsecond=0)
        t_report_end = t_now.replace(hour=16, minute=30, second=0, microsecond=0)
        t_program_exit = t_now.replace(hour=16, minute=30, second=0, microsecond=0)
        today = datetime.datetime.today().weekday()

        if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
             send_message("주말이므로 프로그램을 종료합니다.")
             break

        if t_start <= t_now:
            # time.sleep(10)  # 시가 조회 시간 여유 부여
            if isInit:  # 첫 1회 초기화
                wish_stock_dict = init_trgt_stock_list(symbol_list)
                report_cur_stock_info(dict_bought_list, wish_stock_dict)
                print("=====> " + str(dict_bought_list))
                time.sleep(1)
                isInit = False
            schedule.run_pending()  # 정시에 현재 보유 주식 정보를 보고받고자 스케쥴러 실행
        if t_buy_start <= t_now < t_buy_end:  # 09:02 ~ 09:30 까지만 매수
            print("=====매수목표가 달성 시 매수 진행")
            time.sleep(1)
            buy_stock_by_condition(wish_stock_dict, dict_bought_list)
        if t_sell_start <= t_now < t_sell_end:  # 09:31 ~ 15:20 까지 매도 진행
            # 매수한 종목이 금일 매수금액 대비 2% 이상이면 욕심부리지 말고 팔자. 미반영
            print("=====매도목표가 달성 시 매도 진행")
            time.sleep(1)
            sell_stock_by_condition(wish_stock_dict, dict_bought_list)
        if t_sell_end <= t_now < t_exit:  # PM 03:20 ~ PM 03:30 : 일괄 매도
            if len(dict_bought_list) > 0:
                logger.info("=====일괄매도 진행")
                time.sleep(1)
                sell_stock_all(wish_stock_dict, dict_bought_list)
        if t_report <= t_now <= t_report_end:  # PM 04:00 ~ 04:30
            if not isSaveProfit:
                profit_amt = get_real_profit()
                result_msg = "금일 실현손익 합계: " + str(profit_amt)
                send_message(result_msg)
                write_report(result_msg)
                write_monthly_report(str(profit_amt))

                # 데일리 정보 저장
                try:
                    today = datetime.date.today()
                    ins_daily_report(today.strftime("%Y%m%d"))
                except Exception as e:
                    logger.error(e.args)

                # 데일리 정보 조회
                try:
                    today = datetime.date.today()
                    sel_daily_report(today.strftime("%Y%m%d"))
                except Exception as e:
                    logger.error(e.args)
            isSaveProfit = True
        if t_program_exit <= t_now:
            try:
                today = datetime.date.today()
                upd_charge_amt(today.strftime("%Y%m%d"))
            except Exception as e:
                logger.error(e.args)
            break
    except Exception as e:
        logger.error(e.args)
        send_message(f"[오류 발생]{e}")
