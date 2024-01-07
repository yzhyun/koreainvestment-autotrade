import pymysql
import yaml

with open('././config/config.yaml', encoding='UTF-8') as f:
    _cfg = yaml.load(f, Loader=yaml.FullLoader)

# MySQL 연결 정보
db_config = {
    'host': _cfg['HOST'],
    'user': _cfg['USER'],
    'password': _cfg['PASSWORD'],
    'database': _cfg['DATABASE'],
    'charset': _cfg['CHARSET']
}

def init():
    conn = pymysql.connect(**db_config)
    return conn

def test_db():
    print("DB 테스트")
    conn = init()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM STOCK_MST")
    rows = cur.fetchone()
    print(rows)
    if len(rows) > 0 :
        print("DB 정상")
        return True
    else:
        return False

def select(sql):
    conn = init()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    #print(rows)
    conn.close()
    return rows

def update(sql):
    conn = init()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    print(rows)
    conn.commit()
    conn.close()

def insert(sql):
    conn = init()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()

def delete(sql):
    conn = init()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    conn.commit()
    conn.close()


