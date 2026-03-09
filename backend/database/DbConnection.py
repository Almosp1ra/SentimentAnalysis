import mysql.connector

#建立数据库连接
def ConnectDatabase():
    conn = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = '123456',
        database = 'social_sentiment',
        port=3307
    )
    return conn

