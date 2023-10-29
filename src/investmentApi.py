import KoreaInvestmentApi as kis
from common import *

with open('./config/stock_code.yaml', encoding='UTF-8') as f:
    _code = yaml.load(f, Loader=yaml.FullLoader)

def initInvestement():
    #kis.ACCESS_TOKEN = kis.get_access_token()
    kis.ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6IjI3MWU0MGNlLWM3ZGItNGIyOS04YTY2LWY4MWQyMDY0M2Q4NyIsImlzcyI6InVub2d3IiwiZXhwIjoxNjk4NTY4NTcyLCJpYXQiOjE2OTg0ODIxNzIsImp0aSI6IlBTc1lIdk9yMTBUSkFnbW9uOTN6TWhrUk84ZTZBcHl6YjZubCJ9.0wTT5o3P0VswPXME9PVrif4X8NL3haSnF3TWwYXKEI7g0R66pILkFr01DMJb29kfNxnPyHMV5BOXafkwXr4HfQ"
    print(kis.ACCESS_TOKEN)

# 보유 현금 조회
def getBalanceCash():
    res = kis.get_balance()
    cash = res.json()['output']['ord_psbl_cash']
    return cash


# 보유 주식 조회
def getBalanceStock():
    res = kis.get_stock_balance()
    stock_list = res.json()['output1']
    evaluation = res.json()['output2']
    stock_dict = {}
    for stock in stock_list:
        if int(stock['hldg_qty']) > 0:
            stock_dict[stock['pdno']] = stock['hldg_qty']
    #         send_message(f"{stock['prdt_name']}({stock['pdno']}): {stock['hldg_qty']}주")
    #         time.sleep(0.1)
    # send_message(f"주식 평가 금액: {evaluation[0]['scts_evlu_amt']}원")
    # time.sleep(0.1)
    # send_message(f"평가 손익 합계: {evaluation[0]['evlu_pfls_smtl_amt']}원")
    # time.sleep(0.1)
    # send_message(f"총 평가 금액: {evaluation[0]['tot_evlu_amt']}원")
    # time.sleep(0.1)
    return stock_dict

# 주식 매도
def sellAllStocks(stock_dict, symbol_list):
    failCodes = []
    res = {}
    res["rtnCd"] = "S"
    for code, qty in stock_dict.items():
        if code in symbol_list:  # 매수 희망 종목 리스트에 포함된 주식만 해당 프로그램에서 다룬다.
            try:
                res = kis.sell(code, qty)
                if res.json()['rt_cd'] != '0':
                    logger.error("[매도 실패]")
                    failCodes.append(code)
                    res["rtnCd"] = "F"
            except Exception as e:
                logger.error(f"[매도 오류 발생]{e}")
    res["failCodes"] = failCodes

    return res

def getStockPriceDailyInfo(code):
    res = kis.get_stock_price(code)
    return res

def initTrgtStockList(symbol_list):
    rtnRes = {}
    for code in symbol_list:
        logger.info(f"{_code[code]}[{code}]")
        arr = []
        res = getStockPriceDailyInfo(code)

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
        rtnRes[code] = arr
    return rtnRes