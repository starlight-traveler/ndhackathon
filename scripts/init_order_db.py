# AI helped with syntax for creating the DB

import sqlite3

def create_order_db(db_file='orders.db'):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        children INTEGER,
        adults INTEGER,
        address TEXT,
        fulfilled INTEGER DEFAULT 0 CHECK (fulfilled IN (0,1)),
        restrictions TEXT
    )
    ''')
    conn.commit()
    conn.close()
    
    print("orders.db created")
    
if __name__ == '__main__':
    create_order_db()