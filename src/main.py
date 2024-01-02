import sys, os
import datetime, schedule
from investmentApi import *
from common import *
import time
import mysql as db

#db.select("SELECT * FROM STOCK_MST")
#db.insert("INSERT INTO STOCK_MST VALUES ('11111', 'TEST', '')")
#db.update("DELETE FROM STOCK_MST WHERE STOCK_ID = '11111'")
#db.update("UPDATE STOCK_MST SET CATE_CD = '111' WHERE STOCK_ID = '454910'")


with open('./config/stock_code.yaml', encoding='UTF-8') as f:
    _code = yaml.load(f, Loader=yaml.FullLoader)

# 삼성전자: 005930 카카오: 035720 하이닉스: 000660 세틀뱅크: 234340 현대차: 005380 나이스정보통신: 036800 LG전자: 066570 LG유플러스: 032640
# 한화: 000880 롯데정보통신: 286940 CJ CGV: 079160 롯데지주: 004990 삼천리: 004690 대한항공: 003490 네이버: 035420 두산로보티스: 454910
# symbol_list = [
#       "084730"  # [블랙박스] 팅크웨어
#     #, "158430"  # [보안] 아톤
# #    , "399720" # [반도체] 가온칩스
#     , "005290"  # [반도체] 동진쎄미켐
#     , "126700"  # [2차전지] 하이비젼시스템
#     , "068240"  # [철도] 다원시스
#     , "418470", "053280" # [출판] 밀리의서재, 예스24
#     , "004540", "115390"  # [생활] 깨끗한나라, 락앤락
#     , "042510", "030520"  # [IT] 라온시큐어, 한글과컴퓨터
#     , "039130"  # [여행] 하나투어
#     , "234340", "000660", "035720", "036800", "066570", "032640", "000880", "005380", "286940", "079160", "069960"
#     , "004990", "004690", "003490", "035420", "454910", "323410"]  # 매수 희망 종목 리스트


isReportTime = False    # 중간 보고 용 flag
isInit = True

logger.info("======================Start the program. Let's be rich======================")
send_message("===Start the program. Let's be rich===")

# KIS 초기화
init_investment()
get_daily_ccld()
# 희망 매수 종목 셋팅
symbol_list = init_symbol_list()
wish_stock_dict = {}  # 매수 희망 종목 정보
dict_bought_list = {}  # 매수 완료 정보

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
        t_start = t_now.replace(hour=9, minute=2, second=0, microsecond=0)
        t_buy_start = t_now.replace(hour=9, minute=2, second=0, microsecond=0)
        t_buy_end = t_now.replace(hour=9, minute=30, second=0, microsecond=0)
        t_sell_start = t_now.replace(hour=10, minute=00, second=0, microsecond=0)
        t_sell_end = t_now.replace(hour=15, minute=20, second=0, microsecond=0)
        t_exit = t_now.replace(hour=15, minute=25, second=0, microsecond=0)

        today = datetime.datetime.today().weekday()

        # if today == 5 or today == 6:  # 토요일이나 일요일이면 자동 종료
        #     send_message("주말이므로 프로그램을 종료합니다.")
        #     break
        # if t_9 <= t_now <= t_start:

        if t_start <= t_now:
            # time.sleep(10)  # 시가 조회 시간 여유 부여
            if isInit:  # 첫 1회 초기화
                wish_stock_dict = init_trgt_stock_list(symbol_list)
                print(wish_stock_dict)
                time.sleep(1)
                report_cur_stock_info(dict_bought_list, wish_stock_dict)
                isInit = False
            schedule.run_pending()  # 정시에 현재 보유 주식 정보를 보고받고자 스케쥴러 실행
        if t_buy_start <= t_now < t_buy_end:  # 09:02 ~ 10:00 까지만 매수
            print("=====매수목표가 달성 시 매수 진행")
            time.sleep(1)
            buy_stock_by_condition(wish_stock_dict, dict_bought_list)
        if t_sell_start <= t_now < t_sell_end:  # 10:00 ~ 15:20 까지 매도 진행
            # 매수한 종목이 금일 매수금액 대비 2% 이상이면 욕심부리지 말고 팔자. 미반영
            print("=====매도목표가 달성 시 매도 진행")
            time.sleep(1)
            sell_stock_by_condition(wish_stock_dict, dict_bought_list)
        if t_sell_end <= t_now < t_exit:  # PM 03:20 ~ PM 03:25 : 일괄 매도
            time.sleep(1)
            sell_stock_all(wish_stock_dict, dict_bought_list)
        if t_exit <= t_now:  # PM 03:25 ~ :프로그램 종료
            report_cur_stock_info(dict_bought_list, wish_stock_dict)

            profit_amt = get_real_profit()
            result_msg = "금일 실현손익 합계: " + str(profit_amt)
            send_message(result_msg)
            write_report(result_msg)
            write_monthly_report(str(profit_amt))
            break
    except Exception as e:
        logger.error(e.args)
        send_message(f"[오류 발생]{e}")
