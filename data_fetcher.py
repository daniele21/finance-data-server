import yfinance as yf


def fetch_from_yfinance(ticker_symbol):
    """
    Fetches comprehensive data for a given ticker symbol from Yahoo Finance.
    Returns a dictionary with company info and historical data.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)

        # Fetch company info
        info = ticker.info

        # Check if the ticker is valid by looking for a key like 'shortName'
        if not info.get('shortName'):
            print(f"Could not find info for ticker: {ticker_symbol}")
            return None

        # Fetch historical market data for the last year
        hist = ticker.history(period="1y")

        # yfinance returns timestamps as timezone-aware, which can be tricky with JSON.
        # We convert the index to simple strings.
        hist.index = hist.index.strftime('%Y-%m-%d')

        # Convert DataFrame to dictionary for easy JSON serialization
        hist_dict = hist.to_dict(orient='index')

        # Combine info and history into a single response object
        response_data = {
            'info': info,
            'history': hist_dict
        }

        return response_data

    except Exception as e:
        print(f"An error occurred while fetching data for {ticker_symbol}: {e}")
        return None