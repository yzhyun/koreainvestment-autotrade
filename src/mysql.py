import pymysql
import yaml


with open('./config/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

# MySQL 연결 정보
db_config = {
    'host': _cfg['HOST'],
    'user': _cfg['USER'],
    'password': _cfg['PASSWORD'],
    'database': _cfg['DATABASE'],
    'charset': _cfg['CHARSET'],
}

db_config_dict = {
    'host': _cfg['HOST'],
    'user': _cfg['USER'],
    'password': _cfg['PASSWORD'],
    'database': _cfg['DATABASE'],
    'charset': _cfg['CHARSET'],
    'cursorclass': pymysql.cursors.DictCursor
}

def test_db():
    print("DB 접속 테스트")
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    cur.execute("SELECT STOCK_ID FROM STOCK_MST")
    row = cur.fetchone()
    if len(row) > 0 :
        print("DB 접속 OK")
        return True
    else:
        print("DB 접속 실패")
        return False

def select(sql):
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows
def select_dict(sql):
    conn = pymysql.connect(**db_config_dict)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.close()
    return rows

def update(sql):
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    print(rows)
    conn.commit()
    conn.close()

def insert(sql):
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()

def delete(sql):
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()


