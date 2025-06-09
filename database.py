import sqlite3
import json
from datetime import datetime

DATABASE_NAME = 'ticker_data.db'


def init_db():
    """Initializes the database and creates the 'tickers' table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Table for cached ticker data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickers (
            ticker TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            last_updated TIMESTAMP NOT NULL
        )
    ''')

    # Table for portfolios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolios (
            name TEXT PRIMARY KEY
        )
    ''')

    # Table for transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio TEXT NOT NULL,
            ticker TEXT NOT NULL,
            quantity REAL NOT NULL,
            price REAL NOT NULL,
            date TEXT NOT NULL,
            label TEXT,
            FOREIGN KEY(portfolio) REFERENCES portfolios(name)
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized.")


def get_ticker_data(ticker_symbol):
    """
    Retrieves data for a specific ticker from the database.
    Returns (data, last_updated) tuple or (None, None) if not found.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    # This row_factory allows accessing columns by name
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT data, last_updated FROM tickers WHERE ticker = ?", (ticker_symbol,))
    row = cursor.fetchone()
    conn.close()

    if row:
        # The data is stored as a JSON string, so we parse it back into a Python dict
        data = json.loads(row['data'])
        # The timestamp is stored as a string, so we parse it back into a datetime object
        last_updated = datetime.fromisoformat(row['last_updated'])
        return data, last_updated

    return None, None


def save_ticker_data(ticker_symbol, data):
    """
    Saves or updates the data for a specific ticker in the database.
    The `OR REPLACE` clause handles both new insertions and updates.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    # Serialize the data dictionary into a JSON string for storage
    data_json = json.dumps(data)
    current_time = datetime.now().isoformat()

    cursor.execute('''
        INSERT OR REPLACE INTO tickers (ticker, data, last_updated)
        VALUES (?, ?, ?)
    ''', (ticker_symbol, data_json, current_time))

    conn.commit()
    conn.close()


def create_portfolio(name):
    """Create a portfolio if it doesn't already exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR IGNORE INTO portfolios (name) VALUES (?)",
        (name,)
    )
    conn.commit()
    conn.close()


def save_transactions(portfolio, transactions):
    """Save a list of transactions for a portfolio."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    for t in transactions:
        cursor.execute(
            """
            INSERT INTO transactions (portfolio, ticker, quantity, price, date, label)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                portfolio,
                t.get("ticker"),
                t.get("quantity"),
                t.get("price"),
                t.get("date"),
                t.get("label"),
            ),
        )
    conn.commit()
    conn.close()


def get_transactions(portfolio):
    """Retrieve all transactions for a portfolio."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ticker, quantity, price, date, label FROM transactions WHERE portfolio = ? ORDER BY date",
        (portfolio,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def aggregate_positions(transactions):
    """Return a dict of ticker -> total quantity."""
    positions = {}
    for t in transactions:
        qty = float(t.get("quantity", 0))
        ticker = t.get("ticker")
        positions[ticker] = positions.get(ticker, 0) + qty
    return positions
