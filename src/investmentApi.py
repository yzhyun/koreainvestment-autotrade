import os
import sys
import KoreaInvestmentApi as kis
from common import *
import mysql as db

_code = ""


def init_investment():
    try:
        kis.ACCESS_TOKEN = kis.get_access_token()
        #kis.ACCESS_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJ0b2tlbiIsImF1ZCI6IjY0YWJjZDlkLTFjNTUtNGM3Ni05YjI0LWI1MTczNTNkZTU2YyIsImlzcyI6InVub2d3IiwiZXhwIjoxNzA1OTk1ODgwLCJpYXQiOjE3MDU5MDk0ODAsImp0aSI6IlBTQVNiWWRhMHVXa0FrT1FieFV2TVU4QU4xVVRKeUoyU29UUyJ9.NTb2_j6xL2w7lXPCRznmZMFm4PkTQt74QmpXUrdJ4ZqDFmnAtnOOvwgjtXzB45hgxcStqZTWNJfiCK3i8b2PvA"
        print(kis.ACCESS_TOKEN)
        db.test_db()
        global _code
        res = db.select("SELECT STOCK_ID, STOCK_NM FROM STOCK_MST")
        _code = dict(res)
        print("코드 테스트: " + _code["005930"])

    except Exception as e:
        send_message("===시스템 초기화 실패, 프로그램을 종료 합니다.===")
        sys.exit()
    return


def init_symbol_list():
    symbol_list = []
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
    """ 배열 순서 변경 금지
    0: 오늘 시가
    1: 전일 고가
    2: 전일 저가
    3: 전일 종가
    4: 매수 목표가
    5: 매매 목표가
    6: 손절 목표가 
    7: 가중치
    """
    sort_dict = {}
    try:
        msg = ""
        for code in symbol_list:
            time.sleep(0.2)
            res = get_stock_price_daily_info(code)
            time.sleep(0.2)
            stock_info = get_stock_cur_info(code)

            arr = []
            stck_prpr = stock_info['stck_prpr']  # 현재가
            stck_oprc = int(res.json()['output'][0]['stck_oprc'])  # 오늘 시가
            stck_hgpr = int(res.json()['output'][1]['stck_hgpr'])  # 전일 고가
            stck_lwpr = int(res.json()['output'][1]['stck_lwpr'])  # 전일 저가
            stck_clpr = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가
            # prdy_ctrt = str(res.json()['output'][1]['prdy_ctrt'])  # 전일 대비율

            # 현재가 대비 (현재가-시가-전일종가) 율로 가중치를 계산한다.
            diff = stck_prpr - stck_oprc - stck_clpr
            diff_per_stck_clpr = round(((stck_prpr - stck_clpr) / stck_clpr * 100), 2)
            diff_per_stck_oprc = round(((stck_prpr - stck_oprc) / stck_oprc * 100), 2)
            sort_key = round(diff_per_stck_oprc + diff_per_stck_clpr, 2)

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
            arr.append(stop_loss_price)  # 손절가
            arr.append(sort_key)  # 정렬을 위한 가중치 계산 값

            msg += _code[code] + "[" + code + "]" + "/" \
                   + "\n" \
                   + "전일종가:" + str(stck_clpr) + "/" \
                   + "오늘시가:" + str(stck_oprc) + "/" \
                   + "현재가:" + str(stck_prpr) + "/" \
                   + "\n" \
                   + "매수목표가:" + str(target_price) + "/" \
                   + "매도목표가:" + str(sell_target_price) + "/" \
                   + "손절목표가:" + str(stop_loss_price) + "/" \
                   + "\n"

            rtnRes[code] = arr
        logger.info(msg)
        send_message(msg)
        rtnRes = dict(sorted(rtnRes.items(), key=lambda x: x[1][7], reverse=True))

        msg2 = ""
        for code in rtnRes:
            temp = rtnRes[code]
            msg2 += _code[code] + "/"
        send_message(msg2)
        write_report(msg2)

    except Exception as e:
        logger.error(f"[목표 주식 초기화 오류 발생]{e}")
    return rtnRes


def init_trgt_stock_list_backup(symbol_list):
    rtnRes = {}
    """ 배열 순서 변경 금지
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
        msg = ""
        for code in symbol_list:
            time.sleep(0.2)
            res = get_stock_price_daily_info(code)
            time.sleep(0.2)
            stock_info = get_stock_cur_info(code)

            arr = []
            stck_prpr = stock_info['stck_prpr']                    # 현재가
            stck_oprc = int(res.json()['output'][0]['stck_oprc'])  # 오늘 시가
            stck_hgpr = int(res.json()['output'][1]['stck_hgpr'])  # 전일 고가
            stck_lwpr = int(res.json()['output'][1]['stck_lwpr'])  # 전일 저가
            stck_clpr = int(res.json()['output'][1]['stck_clpr'])  # 전일 종가
            # prdy_ctrt = str(res.json()['output'][1]['prdy_ctrt'])  # 전일 대비율

            # 현재가 대비 (현재가-시가-전일종가) 율로 가중치를 계산한다.
            diff  =  stck_prpr - stck_oprc - stck_clpr
            diff_per_stck_clpr = round(((stck_prpr-stck_clpr)/stck_clpr*100), 2)
            diff_per_stck_oprc = round(((stck_prpr-stck_oprc)/stck_oprc*100), 2)
            sort_key = round(diff_per_stck_oprc + diff_per_stck_clpr, 2)

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
            arr.append(stop_loss_price)  # 손절가
            arr.append(sort_key) # 정렬을 위한 가중치 계산 값

            msg += _code[code] + "[" + code + "]" + "/" \
                   + "\n" \
                   + "전일종가:" + str(stck_clpr) + "/" \
                   + "오늘시가:" + str(stck_oprc) + "/" \
                   + "현재가:" + str(stck_prpr) + "/" \
                   + "\n" \
                   + "매수목표가:" + str(target_price) + "/" \
                   + "매도목표가:" + str(sell_target_price) + "/" \
                   + "손절목표가:" + str(stop_loss_price) + "/" \
                   + "\n"

            rtnRes[code] = arr
        logger.info(msg)
        send_message(msg)
        rtnRes = dict(sorted(rtnRes.items(), key=lambda x: x[1][7], reverse=True))

        msg2 = ""
        for code in rtnRes:
            temp = rtnRes[code]
            msg2 += _code[code] + "/"
        send_message(msg2)

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
                if int(stock['hldg_qty']) > 0:
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
                if int(stock['hldg_qty']) > 0:
                    tmpList = []
                    cur_amt = int(int(stock['pchs_amt']) / int(stock['hldg_qty']))
                    print(f"*{stock['prdt_name']}\n매입[{cur_amt}]/[{stock['hldg_qty']}] / 현재가[{stock['prpr']}] / 평가손익금액[{stock['evlu_pfls_amt']}]\n")
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
        # 매수목표가보다 현재가가 높은 경우 매수 진행
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
                    wish_stock_dict[code][6] = get_target_price(1, current_price, "", "", "")   # 매수 금액으로 손절가 목표 금액 재설정

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
                        write_report(
                            f"[매도 성공]: {_code[code]}({dict_bought_list[code]}) 평가손익금액: {cur_price_info_list[2]}")
                        write_profit_amt(int(cur_price_info_list[2]))
                        del dict_bought_list[code]
                        del wish_stock_dict[code]
                    else:   # 실패한 사유가 없는 코드 (앱에서 매매)인 경우에도 보유 목록에서 제외해서 다음 번에 정상적으로 매매하도록 수정
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
                        write_report(
                            f"[매도 성공]: {_code[code]}({dict_bought_list[code]}) 평가손익금액: {cur_price_info_list[2]}")
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


def ins_daily_report(dd):
    res = kis.get_daily_ccld(dd, dd)
    # res = {'ctx_area_fk100': '68106434^01^20240105^20240105^ ^00^01^                                                              ', 'ctx_area_nk100': '                                                                                                    ', 'output1': [{'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000020437', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '02', 'sll_buy_dvsn_cd_name': '현금매수', 'pdno': '454910', 'prdt_name': '두산로보틱스', 'ord_qty': '1', 'ord_unpr': '0', 'ord_tmd': '090211', 'tot_ccld_qty': '1', 'avg_prvs': '102700', 'cncl_yn': '', 'tot_ccld_amt': '102700', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '02', 'cpbc_ordp_mtrl_dvsn_cd': '11', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000020530', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '02', 'sll_buy_dvsn_cd_name': '현금매수', 'pdno': '234340', 'prdt_name': '헥토파이낸셜', 'ord_qty': '7', 'ord_unpr': '0', 'ord_tmd': '090215', 'tot_ccld_qty': '7', 'avg_prvs': '25650', 'cncl_yn': '', 'tot_ccld_amt': '179550', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '03', 'cpbc_ordp_mtrl_dvsn_cd': '14', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000021078', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '02', 'sll_buy_dvsn_cd_name': '현금매수', 'pdno': '418470', 'prdt_name': '밀리의서재', 'ord_qty': '10', 'ord_unpr': '0', 'ord_tmd': '090241', 'tot_ccld_qty': '10', 'avg_prvs': '19000', 'cncl_yn': '', 'tot_ccld_amt': '190000', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '03', 'cpbc_ordp_mtrl_dvsn_cd': '14', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000031774', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '02', 'sll_buy_dvsn_cd_name': '현금매수', 'pdno': '068290', 'prdt_name': '삼성출판사', 'ord_qty': '9', 'ord_unpr': '0', 'ord_tmd': '091213', 'tot_ccld_qty': '9', 'avg_prvs': '22000', 'cncl_yn': '', 'tot_ccld_amt': '198000', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '02', 'cpbc_ordp_mtrl_dvsn_cd': '11', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000038455', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '02', 'sll_buy_dvsn_cd_name': '현금매수', 'pdno': '039130', 'prdt_name': '하나투어', 'ord_qty': '3', 'ord_unpr': '0', 'ord_tmd': '092012', 'tot_ccld_qty': '3', 'avg_prvs': '53400', 'cncl_yn': '', 'tot_ccld_amt': '160200', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '02', 'cpbc_ordp_mtrl_dvsn_cd': '11', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000063168', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '01', 'sll_buy_dvsn_cd_name': '현금매도', 'pdno': '234340', 'prdt_name': '헥토파이낸셜', 'ord_qty': '7', 'ord_unpr': '0', 'ord_tmd': '100001', 'tot_ccld_qty': '7', 'avg_prvs': '26700', 'cncl_yn': '', 'tot_ccld_amt': '186900', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '03', 'cpbc_ordp_mtrl_dvsn_cd': '14', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000063180', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '01', 'sll_buy_dvsn_cd_name': '현금매도', 'pdno': '418470', 'prdt_name': '밀리의서재', 'ord_qty': '10', 'ord_unpr': '0', 'ord_tmd': '100002', 'tot_ccld_qty': '10', 'avg_prvs': '20410', 'cncl_yn': '', 'tot_ccld_amt': '204100', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '03', 'cpbc_ordp_mtrl_dvsn_cd': '14', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000063195', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '01', 'sll_buy_dvsn_cd_name': '현금매도', 'pdno': '039130', 'prdt_name': '하나투어', 'ord_qty': '3', 'ord_unpr': '0', 'ord_tmd': '100003', 'tot_ccld_qty': '3', 'avg_prvs': '54300', 'cncl_yn': '', 'tot_ccld_amt': '162900', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '02', 'cpbc_ordp_mtrl_dvsn_cd': '11', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000150712', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '01', 'sll_buy_dvsn_cd_name': '현금매도', 'pdno': '068290', 'prdt_name': '삼성출판사', 'ord_qty': '9', 'ord_unpr': '0', 'ord_tmd': '150010', 'tot_ccld_qty': '9', 'avg_prvs': '21100', 'cncl_yn': '', 'tot_ccld_amt': '189900', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '02', 'cpbc_ordp_mtrl_dvsn_cd': '11', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}, {'ord_dt': '20240105', 'ord_gno_brno': '91254', 'odno': '0000157513', 'orgn_odno': '', 'ord_dvsn_name': '시장가', 'sll_buy_dvsn_cd': '01', 'sll_buy_dvsn_cd_name': '현금매도', 'pdno': '454910', 'prdt_name': '두산로보틱스', 'ord_qty': '1', 'ord_unpr': '0', 'ord_tmd': '152002', 'tot_ccld_qty': '1', 'avg_prvs': '101800', 'cncl_yn': '', 'tot_ccld_amt': '101800', 'loan_dt': '', 'ordr_empno': 'OpnAPI', 'ord_dvsn_cd': '01', 'cncl_cfrm_qty': '0', 'rmn_qty': '0', 'rjct_qty': '0', 'ccld_cndt_name': '없음', 'inqr_ip_addr': '182.212.254.019', 'cpbc_ordp_ord_rcit_dvsn_cd': '', 'cpbc_ordp_infm_mthd_dvsn_cd': '', 'infm_tmd': '', 'ctac_tlno': '01041486636', 'prdt_type_cd': '300', 'excg_dvsn_cd': '02', 'cpbc_ordp_mtrl_dvsn_cd': '11', 'ord_orgno': '00000', 'rsvn_ord_end_dt': ''}], 'output2': {'tot_ord_qty': '0', 'tot_ccld_qty': '0', 'tot_ccld_amt': '0', 'prsm_tlex_smtl': '0', 'pchs_avg_pric': '0.0000'}, 'rt_cd': '0', 'msg_cd': 'KIOK0510', 'msg1': '조회가 완료되었습니다                                                           '}
    print(res.json())
    charge_amt = ""
    if res.json()['rt_cd'] == '0':
        stocks = res.json()['output1']
        stocks2 = res.json()['output2']
        charge_amt = stocks2['prsm_tlex_smtl']
        for stock in stocks:
            profit_dd = stock['ord_dt']
            ord_dd = stock['ord_dt']
            ord_tm = stock['ord_tmd']
            sll_buy_dvsn_cd = stock['sll_buy_dvsn_cd']
            stock_id = stock['pdno']
            ord_qty = stock['ord_qty']
            tot_ccld_qty = stock['tot_ccld_qty']
            avg_prvs = stock['avg_prvs']
            tot_ccld_amt = stock['tot_ccld_amt']
            query = f"INSERT INTO PROFIT_INFO (profit_dd, seq_no, ord_dd, ord_tm, sll_buy_dvsn_cd, stock_id, ord_qty, " \
                    f"tot_ccld_qty, avg_prvs, tot_ccld_amt) VALUES('{profit_dd}', (SELECT COALESCE(max(SEQ_NO),0)+1 FROM (SELECT seq_no FROM PROFIT_INFO where profit_dd = {profit_dd}) as a), '{ord_dd}', '{ord_tm}', '{sll_buy_dvsn_cd}', '{stock_id}', {ord_qty}, {tot_ccld_qty}, " \
                    f"{avg_prvs}, {tot_ccld_amt})"
            # 주식 별 결과를 저장한다.
            db.insert(query)
        # 금일 최종 합계를 저장한다.
        ins_daily_report_total(dd, charge_amt)

def upd_charge_amt(dd):
    res = kis.get_daily_ccld(dd, dd)
    print(res.json())
    charge_amt = 0
    if res.json()['rt_cd'] == '0':
        output2 = res.json()['output2']
        charge_amt = output2['prsm_tlex_smtl']
        if int(charge_amt) > 0:
            query = f"""
                    UPDATE DAILY_REPORT
                       SET CHARGE_AMT = {charge_amt}
                     WHERE 1=1
                       AND REPORT_DD = '{dd}'                    
                    """
            db.update(query)

def ins_daily_report_total(dd, charge_amt):
    query = f"""
            INSERT INTO daily_report 
 	        (report_dd, tot_buy_amt, tot_sell_amt, profit_amt, charge_amt, real_profit_amt)
            SELECT  sell.profit_dd as report_dd
                    ,sum(buy.tot_ccld_amt) as tot_buy_amt
                    ,sum(sell.tot_ccld_amt) as tot_sell_amt		
                    ,sum((sell.tot_ccld_amt - buy.tot_ccld_amt)) as profit_amt
                    ,{charge_amt}
                    ,sum((sell.tot_ccld_amt - buy.tot_ccld_amt)) - {charge_amt} as real_profit_amt 		
              FROM 
              (
                    SELECT tot_ccld_amt
                          ,stock_id
                          ,avg_prvs
                          ,profit_dd
                      FROM profit_info
                     where 1=1
                       and profit_dd = '{dd}'
                       and sll_buy_dvsn_cd = '01'
              ) sell,
              (	
                    SELECT tot_ccld_amt
                           ,stock_id
                           ,avg_prvs
                           ,profit_dd
                      FROM profit_info
                     where 1=1
                       and profit_dd = '{dd}'
                       and sll_buy_dvsn_cd = '02'
              ) buy
             WHERE sell.stock_id = buy.stock_id
            """
    db.insert(query)


def sel_daily_report(dd):
    query = f"""
            WITH TMP AS (
            SELECT  sell.stock_id as STOCK_ID		
                    ,(select stock_nm from stock_mst sm where sm.stock_id = sell.stock_id) as STOCK_NM
                    ,(sell.tot_ccld_amt - buy.tot_ccld_amt) as PROFIT
                    ,buy.avg_prvs as BUY_AVG
                    ,sell.avg_prvs as SELL_AVG
                    ,buy.tot_ccld_amt as BUY_TOT_AMT
                    ,sell.tot_ccld_amt as SELL_TOT_AMT
              FROM 
                  (
                        SELECT tot_ccld_amt
                              ,stock_id
                              ,avg_prvs
                              ,profit_dd
                          FROM profit_info
                         where 1=1
                           and profit_dd = '{dd}'
                           and sll_buy_dvsn_cd = '01'
                  ) sell,
                  (	
                        SELECT tot_ccld_amt
                               ,stock_id
                               ,avg_prvs
                               ,profit_dd
                          FROM profit_info
                         where 1=1
                           and profit_dd = '{dd}'
                           and sll_buy_dvsn_cd = '02'
                  ) buy
                 WHERE sell.stock_id = buy.stock_id
            ) 

            SELECT * FROM TMP
            UNION ALL 
             SELECT 'TOTAL' AS STOCK_ID
                    ,'TOTAL' AS STOCK_NM
                    ,SUM(PROFIT)
                    ,SUM(BUY_AVG)
                    ,SUM(SELL_AVG)
                    ,SUM(BUY_TOT_AMT)
                    ,SUM(SELL_TOT_AMT)
               FROM TMP
            """
    stocks = db.select_dict(query)

    msg = "==>금일 수익 내역\n"
    for stock in stocks:
        stock_nm = stock['STOCK_NM']
        buy_amt = int(stock['BUY_AVG'])
        sell_amt = int(stock['SELL_AVG'])
        profit = int(stock['PROFIT'])
        per = round(((sell_amt - buy_amt) / buy_amt * 100), 2)
        msg += f"{stock_nm}: {profit}[{per}]  (매수: {buy_amt} / 매도: {sell_amt}) \n"

    send_message(msg)
    write_report(msg)

    query2 = f"""
            SELECT REPORT_DD, TOT_BUY_AMT, TOT_SELL_AMT, PROFIT_AMT, CHARGE_AMT, REAL_PROFIT_AMT
              FROM DAILY_REPORT 
             WHERE REPORT_DD = '{dd}'
            """
    daily_res = db.select_dict(query2)
    daily_info = daily_res[0]
    report_dd = daily_info["REPORT_DD"]
    real_profit_amt = daily_info["REAL_PROFIT_AMT"]
    tot_buy_amt = daily_info["TOT_BUY_AMT"]
    tot_sell_amt = daily_info["TOT_SELL_AMT"]
    profit_amt = daily_info["PROFIT_AMT"]
    charge_amt = daily_info["CHARGE_AMT"]

    msg2 = f"==>금일[{report_dd}] 최종 수익: {real_profit_amt} " + "\n" + \
           f"총매수: {tot_buy_amt} / 총매도 {tot_sell_amt} / 수수료 {charge_amt}"
    send_message(msg2)
