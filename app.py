from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import database
from functools import wraps
import data_fetcher
import os
from flask_cors import CORS
import gemini_helper
import portfolio
from google.oauth2 import id_token
from google.auth.transport import requests

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:8000",
    "http://localhost:8080",
    "https://portfoliopilot-335283962900.us-west1.run.app"
], supports_credentials=True)

# Ensure the database is set up before the server starts
database.init_db()

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')


def require_google_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"error": "Authorization header is missing"}), 401

        parts = auth_header.split()
        if parts[0].lower() != 'bearer' or len(parts) != 2:
            return jsonify({"error": "Invalid Authorization header format. Must be 'Bearer <token>'"}), 401

        token = parts[1]

        if not GOOGLE_CLIENT_ID:
            print("ERROR: GOOGLE_CLIENT_ID environment variable not set on the server.")
            return jsonify({"error": "Server configuration error"}), 500

        try:
            # Verify the token against Google's public keys.
            # This checks the signature, expiration, and that it was issued to your client ID.
            id_info = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

            # You can optionally store the user info from the token if needed
            # request.user = id_info

            print(f"Authenticated user: {id_info.get('email')}")

        except ValueError as e:
            # This catches invalid tokens (bad signature, expired, wrong audience, etc.)
            print(f"Token validation failed: {e}")
            return jsonify({"error": f"Invalid or expired token: {e}"}), 401

        return f(*args, **kwargs)

    return decorated_function


# Define how old the data can be before we refresh it from the API
CACHE_DURATION = timedelta(hours=24)


@app.route('/api/ticker/<string:ticker_symbol>', methods=['GET'])
@require_google_token
def get_ticker(ticker_symbol):
    """
    API endpoint to get ticker data.
    It first checks the local database (cache). If the data is recent, it's
    served from there. Otherwise, it fetches from yfinance, updates the
    cache, and then serves the data.
    """
    ticker_symbol = ticker_symbol.upper()

    data, source = data_fetcher.fetch_with_cache(ticker_symbol, CACHE_DURATION)

    if not data:
        return jsonify({'error': f'Could not retrieve data for ticker {ticker_symbol}'}), 404

    response = {
        'source': source,
        'ticker': ticker_symbol,
        'data': data
    }

    return jsonify(response)


@app.route('/api/transactions/<string:portfolio_name>', methods=['POST'])
def add_transactions(portfolio_name):
    data = request.get_json(force=True)
    raw = data.get('raw')
    transactions = data.get('transactions')
    if raw:
        try:
            transactions = gemini_helper.parse_transactions(raw)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    if not transactions:
        return jsonify({'error': 'No transactions provided'}), 400
    database.create_portfolio(portfolio_name)
    database.save_transactions(portfolio_name, transactions)
    return jsonify({'status': 'saved', 'count': len(transactions)})


@app.route('/api/transactions/standardize-and-save', methods=['POST'])
def standardize_and_save():
    data = request.get_json(force=True)
    raw = data.get('raw')
    if not raw:
        return jsonify({'error': 'No raw text provided'}), 400
    try:
        transactions = gemini_helper.parse_transactions(raw)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    if not transactions:
        return jsonify({'error': 'No transactions found'}), 400
    by_portfolio = {}
    for t in transactions:
        name = t.get('portfolio')
        if not name:
            return jsonify({'error': 'Portfolio missing in transaction'}), 400
        by_portfolio.setdefault(name, []).append(t)
    for name, txs in by_portfolio.items():
        database.create_portfolio(name)
        database.save_transactions(name, txs)
    return jsonify({'status': 'saved', 'count': len(transactions), 'transactions': transactions})


@app.route('/api/portfolio/<string:portfolio_name>/status', methods=['GET'])
def portfolio_status(portfolio_name):
    status = portfolio.get_portfolio_status(portfolio_name)
    return jsonify(status)


@app.route('/api/portfolio/<string:portfolio_name>/performance', methods=['GET'])
def portfolio_performance(portfolio_name):
    perf = portfolio.get_performance(portfolio_name)
    return jsonify(perf)


if __name__ == '__main__':
    # Run the Flask app
    # In a production environment, you would use a proper WSGI server like Gunicorn
    app.run(host="0.0.0.0", port=5000, debug=True)
