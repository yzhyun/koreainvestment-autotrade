import pymysql

def init():
    conn = pymysql.connect(host="127.0.0.1", user="root", password="1234", db="mysqldb", charset="utf8")
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


