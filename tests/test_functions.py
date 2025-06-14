import unittest
from unittest import mock
import tempfile
import os
import types
import sys
import pandas as pd

import database
import data_fetcher
import gemini_helper
import portfolio
import app


class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        database.DATABASE_NAME = self.tmp.name
        database.init_db()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_save_and_get_ticker_data(self):
        sample = {'a': 1}
        database.save_ticker_data('TEST', sample)
        data, ts = database.get_ticker_data('TEST')
        self.assertEqual(data, sample)
        self.assertIsNotNone(ts)

    def test_transactions_and_aggregate(self):
        database.create_portfolio('p1')
        txs = [{
            'ticker': 'AAA',
            'quantity': 1,
            'price': 10,
            'date': '2020-01-01',
            'label': 'lab'
        }]
        database.save_transactions('p1', txs)
        loaded = database.get_transactions('p1')
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]['ticker'], 'AAA')
        pos = database.aggregate_positions(loaded)
        self.assertEqual(pos, {'AAA': 1.0})


class DataFetcherTestCase(unittest.TestCase):
    def setUp(self):
        class DummyTicker:
            def __init__(self, symbol):
                self.info = {'shortName': 'Test', 'regularMarketPrice': 5}
                self._history = pd.DataFrame({
                    'Date': pd.date_range('2020-01-01', periods=2),
                    'Close': [1, 2]
                }).set_index('Date')
                self._history.index.name = 'Date'
                self.actions = pd.DataFrame({'Action': ['X']}, index=pd.to_datetime(['2020-01-01']))
                self.actions.index.name = 'Date'
                self.dividends = pd.DataFrame({0: [0.1]}, index=pd.to_datetime(['2020-01-01']))
                self.recommendations = pd.DataFrame({'To Grade': ['Buy']}, index=pd.to_datetime(['2020-01-01']))

            def history(self, period='1y'):
                return self._history

        self.ticker_patch = mock.patch('yfinance.Ticker', DummyTicker)
        self.ticker_patch.start()
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        database.DATABASE_NAME = self.tmp.name
        database.init_db()

    def tearDown(self):
        self.ticker_patch.stop()
        os.unlink(self.tmp.name)

    def test_fetch_from_yfinance(self):
        data = data_fetcher.fetch_from_yfinance('AAA')
        self.assertIn('info', data)
        self.assertIn('history', data)
        self.assertIn('events', data)

    def test_fetch_with_cache(self):
        now = pd.Timestamp.now().to_pydatetime()
        with mock.patch('database.get_ticker_data', return_value=({'x': 1}, now)):
            data, src = data_fetcher.fetch_with_cache('AAA')
            self.assertEqual(src, 'CACHE')
            self.assertEqual(data, {'x': 1})
        with mock.patch('database.get_ticker_data', return_value=(None, None)), \
                mock.patch('data_fetcher.fetch_from_yfinance', return_value={'y': 2}) as fetch_mock, \
                mock.patch('database.save_ticker_data') as save_mock:
            data, src = data_fetcher.fetch_with_cache('BBB')
            fetch_mock.assert_called_once()
            save_mock.assert_called_once()
            self.assertEqual(src, 'YAHOO_FINANCE_API')
            self.assertEqual(data, {'y': 2})



class PortfolioTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        database.DATABASE_NAME = self.tmp.name
        database.init_db()
        txs = [
            {'ticker': 'AAA', 'quantity': 1, 'price': 10, 'date': '2020-01-01', 'label': ''},
            {'ticker': 'BBB', 'quantity': 2, 'price': 20, 'date': '2020-01-01', 'label': ''},
        ]
        database.create_portfolio('p1')
        database.save_transactions('p1', txs)

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_portfolio_status_and_performance(self):
        def fake_fetch(ticker, cache_duration=mock.ANY):
            hist = [
                {'Date': '2020-01-01', 'Close': 1 if ticker == 'AAA' else 2},
                {'Date': '2020-01-02', 'Close': 1.1 if ticker == 'AAA' else 2.1},
            ]
            return {'info': {'regularMarketPrice': 5}, 'history': hist}, 'CACHE'

        with mock.patch('data_fetcher.fetch_with_cache', side_effect=fake_fetch):
            status = portfolio.get_portfolio_status('p1')
            self.assertEqual(len(status['holdings']), 2)
            perf = portfolio.get_performance('p1')
            self.assertTrue(len(perf) > 0)


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        database.DATABASE_NAME = self.tmp.name
        database.init_db()
        app.app.config['TESTING'] = True
        self.client = app.app.test_client()

    def tearDown(self):
        os.unlink(self.tmp.name)

    def test_standardize_and_save(self):
        txs = [{
            'ticker': 'AAA',
            'quantity': 1,
            'price': 10,
            'date': '2020-01-01',
            'label': '',
            'portfolio': 'p1'
        }]
        with mock.patch('gemini_helper.parse_transactions', return_value=txs):
            resp = self.client.post('/api/transactions/standardize-and-save', json={'raw': 'text'})
            self.assertEqual(resp.status_code, 200)
            data = resp.get_json()
            self.assertEqual(data['count'], 1)
            saved = database.get_transactions('p1')
            self.assertEqual(len(saved), 1)


if __name__ == '__main__':
    unittest.main()
