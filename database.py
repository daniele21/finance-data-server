import sqlite3
import json
from datetime import datetime

DATABASE_NAME = 'ticker_data.db'


def init_db():
    """Initializes the database and creates the 'tickers' table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    # Create table to store ticker data
    # - ticker: The stock symbol (e.g., 'AAPL')
    # - data: The fetched data, stored as a JSON string
    # - last_updated: The timestamp when the data was last fetched
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickers (
            ticker TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            last_updated TIMESTAMP NOT NULL
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