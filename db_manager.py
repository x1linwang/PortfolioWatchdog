import sqlite3

DB_PATH = "portfolio.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS holdings (username TEXT, ticker TEXT, shares REAL, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()

def login(user, password):
    conn = sqlite3.connect(DB_PATH)
    res = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (user, password)).fetchone()
    conn.close()
    return res

def create_user(user, password):
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO users VALUES (?, ?)", (user, password))
        conn.commit()
        return True
    except: return False

# --- PORTFOLIO LOGIC ---
def add_transaction(username, ticker, shares):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO holdings (username, ticker, shares) VALUES (?, ?, ?)", (username, ticker.upper(), shares))
    conn.commit()
    conn.close()

def get_portfolio(username):
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT ticker, SUM(shares) 
        FROM holdings 
        WHERE username=? 
        GROUP BY ticker 
        HAVING SUM(shares) > 0
    """, (username,)).fetchall()
    conn.close()
    return rows