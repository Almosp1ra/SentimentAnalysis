import mysql.connector

def init_db():
    with open("backend/database/init.sql", "r", encoding="utf-8") as f:
        sql_script = f.read()
    conn = conn = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = '123456',
        port=3307
    )
    cursor = conn.cursor()
    for stmt in sql_script.split(";"):
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_db()