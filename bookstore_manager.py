import sqlite3

DB_NAME = "bookstore.db"


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.executescript(
        '''
    CREATE TABLE IF NOT EXISTS member (
        mid TEXT PRIMARY KEY,
        mname TEXT NOT NULL,
        mphone TEXT NOT NULL,
        memail TEXT
    );

    CREATE TABLE IF NOT EXISTS book (
        bid TEXT PRIMARY KEY,
        btitle TEXT NOT NULL,
        bprice INTEGER NOT NULL,
        bstock INTEGER NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sale (
        sid INTEGER PRIMARY KEY AUTOINCREMENT,
        sdate TEXT NOT NULL,
        mid TEXT NOT NULL,
        bid TEXT NOT NULL,
        sqty INTEGER NOT NULL,
        sdiscount INTEGER NOT NULL,
        stotal INTEGER NOT NULL
    );
    '''
    )
    cursor.execute(
        "INSERT OR IGNORE INTO member VALUES (?, ?, ?, ?)",
        ("M001", "Alice", "0912345678", "alice@example.com"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO book VALUES (?, ?, ?, ?)", ("B001", "Python入門", 500, 10)
    )
    conn.commit()


def add_sale(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    try:
        sdate = input("請輸入銷售日期(YYYY-MM-DD): ").strip()
        if len(sdate) != 10 or sdate.count('-') != 2:
            print("日期格式錯誤！")
            return

        mid = input("請輸入會員編號: ").strip()
        cursor.execute("SELECT * FROM member WHERE mid = ?", (mid,))
        if cursor.fetchone() is None:
            print("查無此會員！")
            return

        bid = input("請輸入書籍編號: ").strip()
        cursor.execute("SELECT * FROM book WHERE bid = ?", (bid,))
        book_row = cursor.fetchone()
        if book_row is None:
            print("查無此書籍！")
            return

        try:
            sqty = int(input("請輸入購買數量: "))
            sdiscount = int(input("請輸入折扣金額: "))
        except ValueError:
            print("數量和折扣必須是整數！")
            return

        if sqty <= 0 or sdiscount < 0:
            print("數量需為正整數，折扣需為非負整數！")
            return

        if book_row['bstock'] < sqty:
            print("庫存不足！")
            return

        stotal = book_row['bprice'] * sqty - sdiscount

        try:
            cursor.execute(
                '''INSERT INTO sale (sdate, mid, bid, sqty, sdiscount, stotal)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                (sdate, mid, bid, sqty, sdiscount, stotal),
            )
            cursor.execute("UPDATE book SET bstock = bstock - ? WHERE bid = ?", (sqty, bid))
            conn.commit()
            print("銷售紀錄新增成功！")
        except sqlite3.Error:
            conn.rollback()
            print("新增失敗，已回復交易")
    except sqlite3.DatabaseError as e:
        print("資料庫錯誤：", e)


def print_sale_report(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        '''
    SELECT  sale.sid, sale.sdate, member.mname, book.btitle, book.bprice,
            sale.sqty, sale.sdiscount, sale.stotal
    FROM sale
    JOIN member ON sale.mid = member.mid
    JOIN book ON sale.bid = book.bid
    ORDER BY sale.sid
    '''
    )
    rows = cursor.fetchall()
    print("\n==================== 銷售報表 ====================")
    for i, row in enumerate(rows, 1):
        print(f"銷售 #{i}")
        print(f"銷售編號: {row['sid']}")
        print(f"銷售日期: {row['sdate']}")
        print(f"會員姓名: {row['mname']}")
        print(f"書籍標題: {row['btitle']}")
        print("--------------------------------------------------")
        print("單價\t數量\t折扣\t小計")
        print("--------------------------------------------------")
        print(f"{row['bprice']:,}\t{row['sqty']}\t{row['sdiscount']:,}\t{row['stotal']:,}")
        print("--------------------------------------------------")
        print(f"銷售總額: {row['stotal']:,}")
        print("==================================================")


def update_sale(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    try:
        sid = input("請輸入要更新的銷售編號: ").strip()
        cursor.execute("SELECT * FROM sale JOIN book ON sale.bid = book.bid WHERE sid = ?", (sid,))
        row = cursor.fetchone()
        if row is None:
            print("查無此銷售紀錄！")
            return

        try:
            new_discount = int(input("請輸入新的折扣金額: "))
        except ValueError:
            print("折扣金額必須是整數！")
            return

        new_total = row['bprice'] * row['sqty'] - new_discount

        cursor.execute(
            "UPDATE sale SET sdiscount = ?, stotal = ? WHERE sid = ?",
            (new_discount, new_total, sid),
        )
        conn.commit()
        print("銷售紀錄更新成功！")
    except sqlite3.Error:
        conn.rollback()
        print("更新失敗，已回復交易")


def delete_sale(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    try:
        sid = input("請輸入要刪除的銷售編號: ").strip()
        cursor.execute("SELECT * FROM sale WHERE sid = ?", (sid,))
        row = cursor.fetchone()
        if row is None:
            print("查無此銷售紀錄！")
            return

        cursor.execute(
            "UPDATE book SET bstock = bstock + ? WHERE bid = ?", (row['sqty'], row['bid'])
        )
        cursor.execute("DELETE FROM sale WHERE sid = ?", (sid,))
        conn.commit()
        print("銷售紀錄刪除成功！")
    except sqlite3.Error:
        conn.rollback()
        print("刪除失敗，已回復交易")


def main() -> None:
    with connect_db() as conn:
        initialize_db(conn)
        while True:
            print(
                """
***************選單***************
1. 新增銷售記錄
2. 顯示銷售報表
3. 更新銷售記錄
4. 刪除銷售記錄
5. 離開
**********************************
            """
            )
            choice = input("請選擇操作項目(Enter 離開)：").strip()
            if choice in ("", "5"):
                break
            elif choice == "1":
                add_sale(conn)
            elif choice == "2":
                print_sale_report(conn)
            elif choice == "3":
                update_sale(conn)
            elif choice == "4":
                delete_sale(conn)
            else:
                print("=> 請輸入有效的選項（1-5）")


if __name__ == "__main__":
    main()
