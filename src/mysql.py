import pymysql

# MySQL 연결 정보
db_config = {
    'host': "127.0.0.1",
    'user': "root",
    'password': "1234",
    'database': "richdev",
    'charset': "utf8"
}

def init():
    conn = pymysql.connect(**db_config)
    return conn

def test_db():
    conn = init()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM STOCK_MST")
    rows = cur.fetchone()
    print(rows)
    if len(rows) > 0 :
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


