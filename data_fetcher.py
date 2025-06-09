import yfinance as yf
import pandas as pd

def fetch_from_yfinance(ticker_symbol):
    """
    Fetches comprehensive data for a given ticker symbol from Yahoo Finance.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info

        if not info.get('shortName'):
            print(f"Could not find info for ticker: {ticker_symbol}")
            return None

        hist = ticker.history(period="1y")

        # --- THE FIX IS HERE ---
        # Pandas' to_json method correctly handles NaN -> null conversion.
        # We will convert the DataFrame to a JSON string first, then parse it back
        # into a Python dictionary. This cleans the data.

        # Replace non-finite values (NaN, inf, -inf) with None (which becomes null in JSON)
        hist = hist.where(pd.notna(hist), None)

        # Convert the cleaned DataFrame to a dictionary
        hist.index = hist.index.strftime('%Y-%m-%d')
        hist_dict = hist.to_dict(orient='index')
        # --- END FIX ---

        response_data = {
            'info': info,
            'history': hist_dict
        }

        return response_data

    except Exception as e:
        print(f"An error occurred while fetching data for {ticker_symbol}: {e}")
        return None

    except Exception as e:
        print(f"An error occurred while fetching data for {ticker_symbol}: {e}")
        return None