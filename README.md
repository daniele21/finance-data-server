# Finance Data Server

This small Flask application exposes an API to fetch stock data using [yfinance](https://github.com/ranaroussi/yfinance). Requests to `/api/ticker/<symbol>` return cached data about the requested ticker. The fetched data now includes:

- `info` – basic company information
- `history` – one year of daily price history
- `events.actions` – dividends and stock split events
- `events.dividends` – dividend payments
- `events.recommendations` – analyst recommendation history

The server caches responses in a local SQLite database for 24 hours to limit calls to Yahoo Finance.
The helper ``fetch_with_cache`` in ``data_fetcher.py`` encapsulates this logic and returns cached data when available.

Portfolio calculations also reuse this cached ticker history so repeated requests do not refetch large datasets.

## Portfolio Management

Additional endpoints provide simple portfolio tracking. A Gemini API key is read
from the ``GEMINI_API_KEY`` environment variable to allow transaction text to be
parsed via Google Gemini.  The model used can be overridden by setting
``GEMINI_MODEL`` (default ``gemini-pro``).

- ``POST /api/transactions/<portfolio>`` – Accepts either ``{"raw": "..."}`` or
  ``{"transactions": [...]}``. Raw text is sent to Gemini to extract
  standardized transactions, which are then stored in the database.
- ``GET /api/portfolio/<portfolio>/status`` – Returns current holdings with the
  latest market price for each asset.
- ``GET /api/portfolio/<portfolio>/performance`` – Calculates a simple time
  series of portfolio value based on daily closing prices.

## Testing

Unit tests can be run with:

```
python -m unittest discover -s tests -v
```

The optional integration test ``tests/test_gemini_integration.py`` makes a real
call to Gemini. Set ``GEMINI_API_KEY`` and optionally ``GEMINI_MODEL`` to enable
this test.
