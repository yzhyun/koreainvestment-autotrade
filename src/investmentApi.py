import KoreaInvestmentApi as kis
from common import *

with open('./config/stock_code.yaml', encoding='UTF-8') as f:
    _code = yaml.load(f, Loader=yaml.FullLoader)


def init_investment():
    kis.ACCESS_TOKEN = kis.get_access_token()
    #kis.ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6IjI3Zjg4MmQyLWQ5YzAtNDgzNi04MzEyLWYxYjM0NjkyYWMwNiIsImlzcyI6InVub2d3IiwiZXhwIjoxNjk5NTM0NTIwLCJpYXQiOjE2OTk0NDgxMjAsImp0aSI6IlBTc1lIdk9yMTBUSkFnbW9uOTN6TWhrUk84ZTZBcHl6YjZubCJ9.MQxK5L0-vuh8y1Bb-Vr5xWwD2z65aR2faJB2nMooV43Uaw9lDhl-018-qzd5wTdMqvnp1WAIHZ0kyo1_-KIUSg"
    print(kis.ACCESS_TOKEN)


# 보유 현금 조회
def get_balance_cash():
    try:
        res = kis.get_balance()
        print(res.text)
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
        if res.json()['rt_cd'] == '0':
            return True
    except Exception as e:
        logger.error(f"[주식매매 오류 발생]{e}")
    return False


def sell_stock(code, buy_qty):
    try:
        res = kis.sell(code, buy_qty)
        if res.json()['rt_cd'] == '0':
            return True
    except Exception as e:
        logger.error(f"[주식매매 오류 발생]{e}")

    return False


def init_trgt_stock_list(symbol_list):
    rtnRes = {}
    """ 
    0: 오늘 시가
    1: 전일 고가
    2: 전일 저가
    3: 전일 종가
    4: 매수 목표가
    5: 매매 목표가    
    """
    try:
        for code in symbol_list:
            logger.info(f"{_code[code]}[{code}]")
            arr = []
            res = get_stock_price_daily_info(code)
            # res2 = get_stock_cur_price(code)
            # print(res2)
            # 주식 현재가 조회로 변경해야할 것 같은데..?
    
            stck_oprc = int(res.json()['output'][0]['stck_oprc'])  # 오늘 시가
            stck_hgpr = int(res.json()['output'][1]['stck_hgpr'])  # 전일 고가
            stck_lwpr = int(res.json()['output'][1]['stck_lwpr'])  # 전일 저가
            stck_clpr = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가
    
            # 0 : 시가의 1% 상승 시 목표가
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
    
            msg = _code[code] + "[" + code + "]" + "\n" + "오늘 시가: " + str(stck_oprc) + "\n" + "전일 종가: " \
                  + str(stck_clpr) + "\n" + "매수목표가: " + str(target_price) + "\n" + "매도목표가: " + str(
                sell_target_price)
            send_message(msg)
            rtnRes[code] = arr
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
                stock_amt = int(int(stock['pchs_amt']) / int(stock['hldg_qty']))
                # rate = (int(stock['prpr']) - int(arrTmp[0])) / int(arrTmp[0])
                sMessage += f"*{stock['prdt_name']}\n매입[{stock_amt}]*[{stock['hldg_qty']}] / 현재가[{stock['prpr']}] / 매수목표가[{arrTmp[4]}] / 매매목표가[{arrTmp[5]}] / 평가손익금액[{stock['evlu_pfls_amt']} / 평균매입금액[{int(stock['pchs_avg_pric'])}]\n"
                dict_bought_list[stock['pdno']] = stock['hldg_qty']
                sum_pfls_amt += int(stock['evlu_pfls_amt'])
        write_report(f"{sMessage}\n총평가손익금액: {sum_pfls_amt}")
        send_message(f"{sMessage}\n총평가손익금액: {sum_pfls_amt}")
    except Exception as e:
        logger.error(f"[레포트 오류 발생]{e}")
    logger.info("=====reportCurStockInfo END =====")
    return True


def get_my_stock_cur_amt(wish_stock_dict):
    try:
        rtnRes = {}
        tmpList = []
        res = kis.get_stock_balance()
        stock_list = res.json()['output1']
        evaluation = res.json()['output2']

        for stock in stock_list:
            if stock['pdno'] in wish_stock_dict.keys():
                print(
                    f"*{stock['prdt_name']}\n매입[{stock['pchs_amt']}]/[{stock['hldg_qty']}] / 현재가[{stock['prpr']}] / 평가손익금액[{stock['evlu_pfls_amt']}]\n")
                rtnRes[stock['pdno']] = stock['prpr']
    except Exception as e:
        logger.error(f"[보유 주식 현재가 조회 오류 발생]{e}")
    return rtnRes
