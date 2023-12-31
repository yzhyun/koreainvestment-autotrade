import os
import sys
import KoreaInvestmentApi as kis
from common import *
import mysql as db

# 코드 정보 Load
# with open('./config/stock_code.yaml', encoding='UTF-8') as f:
#     _codes = yaml.load(f, Loader=yaml.FullLoader)

_code = ""
def init_investment():
    try:
        kis.ACCESS_TOKEN = kis.get_access_token()
        #kis.ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6IjA4ODM1MGNjLWU5ODQtNGVjMS05ZjE2LTNiMjQ0NjRhODEzYSIsImlzcyI6InVub2d3IiwiZXhwIjoxNzA0Mjg0NTgzLCJpYXQiOjE3MDQxOTgxODMsImp0aSI6IlBTQVNiWWRhMHVXa0FrT1FieFV2TVU4QU4xVVRKeUoyU29UUyJ9.CFGSpjytShzM7GcFhJkJm_9Rm7KQABZEM1IZgs_WtdOLzMVGv8xZ0D7JKoLxQcPgSaUOVU6ZwMIl8ysQLTIYkQ"
        print(kis.ACCESS_TOKEN)
        db.test_db()
        global _code
        res = db.select("SELECT STOCK_ID, STOCK_NM FROM STOCK_MST")
        _code = dict(res)
    except Exception as e:
        send_message("===시스템 초기화 실패, 프로그램을 종료 합니다.===")
        sys.exit()
    return

def init_symbol_list():
    symbol_list= []
    res = db.select("SELECT A.STOCK_ID "
                    ",(SELECT STOCK_NM FROM STOCK_MST WHERE STOCK_ID = A.STOCK_ID) AS STOCK_NM "              
                    "FROM wish_stock_mst A "
                    "WHERE WISH_YN = 'Y' ")
    for info in res:
        symbol_list.append(info[0])

    return symbol_list

# 보유 현금 조회
def get_balance_cash():
    try:
        res = kis.get_balance()
        cash = res.json()['output']['ord_psbl_cash']
    except Exception as e:
        logger.error(f"[보유 현금 조회 오류 발생]{e}")
    return int(cash)


# 주식 전체 매도
# def sell_all_stocks(stock_dict, wish_stock_dict):
#     failCodes = []
#     res = {}
#     res["rtnCd"] = "S"
#     for code, qty in stock_dict.items():
#         if code in wish_stock_dict.keys():  # 매수 희망 종목 리스트에 포함된 주식만 해당 프로그램에서 다룬다.
#             try:
#                 res = kis.sell(code, qty)
#                 if res.json()['rt_cd'] != '0':
#                     logger.error("[매도 실패]" + res.json()['msg'])
#                     failCodes.append(code)
#                     res["rtnCd"] = "F"
#             except Exception as e:
#                 logger.error(f"[매도 오류 발생]{e}")
#     res["failCodes"] = failCodes
# 
#     return res


def get_stock_price_daily_info(code):
    res = ""
    try:
        res = kis.get_stock_price(code)
    except Exception as e:
        logger.error(f"[주식 일별 정보 조회 오류 발생]{e}")
    return res


def get_stock_cur_price(code):
    try:
        res = kis.get_current_price(code)
        time.sleep(1)
    except Exception as e:
        logger.error(f"[주식 현재가 조회 오류 발생]{e}")
    return res


def buy_stock(code, buy_qty):
    try:
        res = kis.buy(code, buy_qty)
        print(res.text)
        if res.json()['rt_cd'] == '0':
            return True
    except Exception as e:
        logger.error(f"[주식매매 오류 발생]{e}")
    return False


def sell_stock(code, buy_qty):
    try:
        res = kis.sell(code, buy_qty)
        print(res.text)
        if res.json()['rt_cd'] == '0':
            return True
    except Exception as e:
        logger.error(f"[주식매매 오류 발생]{e}")

    return False


def get_stock_cur_info(code):
    rtnRes = {}
    try:
        res = kis.get_current_stock_info(code)
        stck_oprc = int(res.json()['output']['stck_oprc'])
        stck_prpr = int(res.json()['output']['stck_prpr'])
        rtnRes['stck_oprc'] = stck_oprc
        rtnRes['stck_prpr'] = stck_prpr

    except Exception as e:
        logger.error(f"[주식 현재 정보 조회 오류 발생]{e}")
    return rtnRes
def init_trgt_stock_list(symbol_list):
    rtnRes = {}
    """ 
    0: 오늘 시가
    1: 전일 고가
    2: 전일 저가
    3: 전일 종가
    4: 매수 목표가
    5: 매매 목표가
    6: 손절 목표가    
    """
    sort_dict = {}
    try:
        # 초기화 시, 현재가-시가 높은 순서대로 정렬, 매매 할 수 있도록 한다.
        for code in symbol_list:
            logger.info(f"{_code[code]}[{code}]")
            stock_info = get_stock_cur_info(code)
            time.sleep(0.2)
            diff = stock_info['stck_prpr'] - stock_info['stck_oprc']
            sort_dict[code] = diff
        sort_dict = dict(sorted(sort_dict.items(), key = lambda x : x[1], reverse=True))
        time.sleep(0.2)
        msg = ""
        for code in list(sort_dict.keys()):

            time.sleep(0.2)
            res = get_stock_price_daily_info(code)

            arr = []
            stck_oprc = int(res.json()['output'][0]['stck_oprc'])  # 오늘 시가
            stck_hgpr = int(res.json()['output'][1]['stck_hgpr'])  # 전일 고가
            stck_lwpr = int(res.json()['output'][1]['stck_lwpr'])  # 전일 저가
            stck_clpr = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가

            # 0 : 시가의 1% 상승 시 목표가
            target_price = int(get_target_price(0, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr))
            sell_target_price = int(target_price + target_price * SELL_PER)

            # 손절 목표가 (시가의 5%)
            stop_loss_price = int(get_target_price(1, stck_oprc, stck_hgpr, stck_lwpr, stck_clpr))

            arr.append(stck_oprc)  # 오늘 시가
            arr.append(stck_hgpr)  # 전일 고가
            arr.append(stck_lwpr)  # 전일 저가
            arr.append(stck_clpr)  # 전일 종가
            arr.append(target_price)  # 매수 목표가
            arr.append(sell_target_price)  # 매매 목표가
            arr.append(stop_loss_price) # 손절가

            logger.info(f"오늘 시가: {stck_oprc}")
            logger.info(f"전일 고가: {stck_hgpr}")
            logger.info(f"전일 저가: {stck_lwpr}")
            logger.info(f"전일 종가: {stck_clpr}")
            logger.info(f"매수 목표가:    {target_price}")
            logger.info(f"매도 목표가:    {sell_target_price}")
            logger.info(f"손절 목표가:    {stop_loss_price}")
            # write_profit_amt(stck_oprc)

            msg += _code[code] + "[" + code + "]" + "/" \
                  + "오늘 시가: " + str(stck_oprc) + "/" \
                  + "전일 종가: " + str(stck_clpr) + "/" \
                  + "매수목표가: " + str(target_price) + "/" \
                  + "매도목표가: " + str(sell_target_price) + "/" \
                  + "손절목표가: " + str(stop_loss_price) + "/" \
                  + "\n"
            rtnRes[code] = arr
        send_message(msg)

    except Exception as e:
        logger.error(f"[목표 주식 초기화 오류 발생]{e}")
    return rtnRes


def report_cur_stock_info(dict_bought_list, wish_stock_dict):
    logger.info("=====reportCurStockInfo START =====")
    try:
        res = kis.get_stock_balance()
        stock_list = res.json()['output1']
        evaluation = res.json()['output2']

        t_now = datetime.datetime.now()
        sMessage = "보유주식: \n"
        sum_pfls_amt = 0
        for stock in stock_list:
            if stock['pdno'] in wish_stock_dict.keys():
                arrTmp = wish_stock_dict[stock['pdno']]
                pchs_amt = int(int(stock['pchs_amt']) / int(stock['hldg_qty']))
                cur_rate = round(((int(stock['prpr']) - pchs_amt) / pchs_amt * 100), 2)
                sMessage += f"*{stock['prdt_name']}\n" \
                            f"매입[{pchs_amt}]*[{stock['hldg_qty']}] / 현재가[{stock['prpr']}] / 증감율[{cur_rate}%]\n" \
                            f"매수목표가[{arrTmp[4]}] / 매매목표가[{arrTmp[5]}]\n" \
                            f"평가손익금액[{stock['evlu_pfls_amt']}]\n\n"
                dict_bought_list[stock['pdno']] = stock['hldg_qty']
                sum_pfls_amt += int(stock['evlu_pfls_amt'])

        # write_report(f"{sMessage}총평가손익금액: {sum_pfls_amt}")
        send_message(f"{sMessage}총평가손익금액: {sum_pfls_amt}")
    except Exception as e:
        logger.error(f"[레포트 오류 발생]{e}")
    logger.info("=====reportCurStockInfo END =====")
    return True


def get_my_stock_cur_amt(wish_stock_dict):
    try:
        rtnRes = {}

        res = kis.get_stock_balance()
        stock_list = res.json()['output1']
        evaluation = res.json()['output2']

        for stock in stock_list:
            if stock['pdno'] in wish_stock_dict.keys():
                tmpList = []
                cur_amt = int(int(stock['pchs_amt']) / int(stock['hldg_qty']))
                print(
                    f"*{stock['prdt_name']}\n매입[{cur_amt}]/[{stock['hldg_qty']}] / 현재가[{stock['prpr']}] / 평가손익금액[{stock['evlu_pfls_amt']}]\n")
                tmpList.append(stock['prpr'])  # [0] 현재가
                tmpList.append(stock['hldg_qty'])  # [1] 수량
                tmpList.append(stock['evlu_pfls_amt'])  # [2] 평가손익금액
                rtnRes[stock['pdno']] = tmpList
    except Exception as e:
        logger.error(f"[보유 주식 현재가 조회 오류 발생]{e}")
    return rtnRes


def get_real_profit():
    try:
        today = datetime.date.today()
        filepath = 'report/profit_' + str(today)
        if os.path.isfile(filepath + ".txt"):
            sys.stdin = open(filepath + ".txt", "rt")
            input = sys.stdin.readline
            profit_amt_list = list(map(int, input().split()))
            profit_amt = sum(profit_amt_list)
        else:
            profit_amt = 0
    except Exception as e:
        logger.error(f"[실현손익 조회 오류 발생]{e}")
    return profit_amt


def buy_stock_by_condition(wish_stock_dict, dict_bought_list):
    for code in list(wish_stock_dict.keys()):
        arrTmp = wish_stock_dict[code]
        if code in dict_bought_list:
            logger.info(f"{_code[code]}=====이미 매수한 종목 입니다.")
            continue

        # 종목 현재가 조회
        current_price = get_stock_cur_price(code)
        logger.info(f"{_code[code]} 현재가 [{current_price}] / 매수목표가 [{arrTmp[4]}]")
        
        if len(dict_bought_list) >= MAX_STOCK_NUM:
            print(f"매수 목표량 도달")
            return
        buy_qty = 0
        # 목표가보다 현재가가 높은 경우 매수 진행
        if arrTmp[4] <= current_price:
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

def sell_stock_by_condition(wish_stock_dict, dict_bought_list):
    dict_cur_amt = get_my_stock_cur_amt(wish_stock_dict)  # 매수 종목 현재가 가져오기
    if len(dict_cur_amt) == 0:
        return 0
    for code in list(wish_stock_dict.keys()):
        if code in dict_bought_list:
            arrTmp = wish_stock_dict[code]
            cur_price_info_list = dict_cur_amt[code]
            cur_amt = int(cur_price_info_list[0])
            logger.info(
                f"{_code[code]} 현재가 [{cur_amt} * {cur_price_info_list[1]}] / 매도목표가 [{arrTmp[5]}] / 평가손익금액 [{cur_price_info_list[2]}]")
            if int(arrTmp[5]) <= int(cur_price_info_list[0]):
                send_message(f"{_code[code]} 목표가 달성({arrTmp[4]} <= {cur_price_info_list[0]}) 매도를 시도합니다.")
                try:
                    if sell_stock(code, dict_bought_list[code]):
                        send_message(f"[매도 성공]: {_code[code]}({dict_bought_list[code]})")
                        write_report(f"[매도 성공]: {_code[code]}({dict_bought_list[code]}) 평가손익금액: {cur_price_info_list[2]}")
                        write_profit_amt(int(cur_price_info_list[2]))
                        del dict_bought_list[code]
                        del wish_stock_dict[code]
                except Exception as e:
                    logger.error(f"[매도 오류 발생]{e}")
            # 손절 체크 로직
            if int(arrTmp[6]) >= int(cur_price_info_list[0]):
                send_message(f"{_code[code]} 손절가 도달({arrTmp[4]} <= {cur_price_info_list[0]}) 매도를 시도합니다.")
                try:
                    if sell_stock(code, dict_bought_list[code]):
                        send_message(f"[매도 성공]: {_code[code]}({dict_bought_list[code]})")
                        write_report(f"[매도 성공]: {_code[code]}({dict_bought_list[code]}) 평가손익금액: {cur_price_info_list[2]}")
                        write_profit_amt(int(cur_price_info_list[2]))
                        del dict_bought_list[code]
                        del wish_stock_dict[code]
                except Exception as e:
                    logger.error(f"[매도 오류 발생]{e}")
    return

def sell_stock_all(wish_stock_dict, dict_bought_list):
    dict_cur_amt = get_my_stock_cur_amt(wish_stock_dict)  # 매수 종목 현재가 가져오기
    if len(dict_cur_amt) == 0:
        return 0
    for code in list(wish_stock_dict.keys()):
        if code in dict_bought_list:
            arrTmp = wish_stock_dict[code]
            cur_price_info_list = dict_cur_amt[code]
            logger.info(
                f"{_code[code]} 현재가 [{cur_price_info_list[0]} * {cur_price_info_list[1]}] / 매도목표가 [{arrTmp[5]}] / 평가손익금액 [{cur_price_info_list[2]}]")
            send_message(f"{_code[code]} 목표가 달성({arrTmp[4]} <= {cur_price_info_list[0]}) 매도를 시도합니다.")
            try:
                if sell_stock(code, dict_bought_list[code]):
                    send_message(f"[매도 성공]: {_code[code]}({dict_bought_list[code]})")
                    write_report(
                        f"[매도 성공]: {_code[code]}({dict_bought_list[code]}) 평가손익금액: {cur_price_info_list[2]}")
                    write_profit_amt(int(cur_price_info_list[2]))
                    del dict_bought_list[code]
                    del wish_stock_dict[code]
            except Exception as e:
                logger.error(f"[매도 오류 발생]{e}")
    return

def get_daily_ccld():
    print("get_daily_ccld")
    print(kis.get_daily_ccld("20240102", "20240102"))
