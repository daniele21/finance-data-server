from flask import Flask, jsonify, request
from datetime import datetime, timedelta
import database
from functools import wraps
import data_fetcher
import os
from flask_cors import CORS

app = Flask(__name__)

CORS(app, origins=[
    "http://localhost:8000",
    "http://localhost:8080",
    "https://finance-data-server-335283962900.europe-west1.run.app"
], supports_credentials=True)

# Ensure the database is set up before the server starts
database.init_db()

# Define how old the data can be before we refresh it from the API
CACHE_DURATION = timedelta(hours=24)


# def require_api_key(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         # Read the secret key from environment variables
#         expected_api_key = os.environ.get('API_KEY')
#
#         # Ensure the environment variable is set
#         if not expected_api_key:
#             return jsonify({"error": "API key not configured on server"}), 500
#
#         # Get the API key from the request header
#         provided_key = request.headers.get('X-API-Key')
#         if not provided_key or provided_key != expected_api_key:
#             return jsonify({"error": "Unauthorized"}), 401
#
#         return f(*args, **kwargs)
#
#     return decorated_function

# @require_api_key
@app.route('/api/ticker/<string:ticker_symbol>', methods=['GET'])
def get_ticker(ticker_symbol):
    """
    API endpoint to get ticker data.
    It first checks the local database (cache). If the data is recent, it's
    served from there. Otherwise, it fetches from yfinance, updates the
    cache, and then serves the data.
    """
    ticker_symbol = ticker_symbol.upper()

    # 1. Try to get data from our database (cache)
    cached_data, last_updated = database.get_ticker_data(ticker_symbol)

    source = 'CACHE'  # To indicate where the data came from

    if cached_data:
        # Check if the cached data is still valid
        if datetime.now() - last_updated < CACHE_DURATION:
            print(f"Serving '{ticker_symbol}' data from CACHE.")
            response = {
                'source': source,
                'ticker': ticker_symbol,
                'data': cached_data
            }
            return jsonify(response)
        else:
            print(f"Cache for '{ticker_symbol}' is STALE. Fetching new data.")
    else:
        print(f"No cache found for '{ticker_symbol}'. Fetching new data.")

    # 2. If no valid cache, fetch from Yahoo Finance
    source = 'YAHOO_FINANCE_API'
    fresh_data = data_fetcher.fetch_from_yfinance(ticker_symbol)

    if not fresh_data:
        return jsonify({'error': f'Could not retrieve data for ticker {ticker_symbol}'}), 404

    # 3. Save the newly fetched data to our database
    database.save_ticker_data(ticker_symbol, fresh_data)
    print(f"Saved fresh data for '{ticker_symbol}' to database.")

    response = {
        'source': source,
        'ticker': ticker_symbol,
        'data': fresh_data
    }

    return jsonify(response)


if __name__ == '__main__':
    # Run the Flask app
    # In a production environment, you would use a proper WSGI server like Gunicorn
    app.run(host='0.0.0.0', port=5000, debug=True)