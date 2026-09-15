import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer
from provider_fpa.web import Handler


class WebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def get(self, path):
        with urlopen(self.url + path) as response:
            return response.read()

    def test_readonly_benchmarks_cannot_change_baseline(self):
        before = self.get('/api/baseline')
        for ticker in ('HCA', 'THC'):
            company = json.loads(self.get('/api/benchmarks/' + ticker))
            self.assertEqual(company['ticker'], ticker)
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(self.url + '/api/benchmarks/' + ticker, data=b'{}'))
            self.assertEqual(error.exception.code, 501)
            error.exception.close()
        self.assertEqual(before, self.get('/api/baseline'))

    def test_only_explicit_demo_assets_are_served(self):
        for path in ('/', '/app.js', '/style.css'):
            self.assertTrue(self.get(path))
        for path in ('/.git/config', '/data/synthetic/scenario/clinic_baseline.json', '/api/benchmarks/UNKNOWN'):
            with self.assertRaises(HTTPError) as error:
                self.get(path)
            self.assertEqual(error.exception.code, 404)
            error.exception.close()
