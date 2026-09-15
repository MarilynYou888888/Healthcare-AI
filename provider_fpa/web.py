"""Local-only demo server. Serves explicit assets and read-only financial views."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from provider_fpa.benchmark import load_company
from provider_fpa.scenario import load_baseline

WEB = Path(__file__).resolve().parents[1] / 'web'
ASSETS = {'/executive.js':('executive.js','text/javascript'),'/interpretation.js':('interpretation.js','text/javascript'),'/scenario-view.js':('scenario-view.js','text/javascript'),'/scenario.js':('scenario.js','text/javascript'),'/vendor/decimal.mjs':('vendor/decimal.mjs','text/javascript'),'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if path == '/api/baseline':
                body, content = json.dumps(load_baseline().payload()).encode(), 'application/json'
            elif path in ('/api/benchmarks/HCA','/api/benchmarks/THC'):
                body, content = json.dumps(load_company(path.rsplit('/',1)[-1]).payload()).encode(), 'application/json'
            elif path in ASSETS:
                name,content = ASSETS[path]
                body = (WEB/name).read_bytes()
            else:
                self.send_error(404)
                return
        except (OSError,ValueError,KeyError):
            self.send_error(503,'Reference data unavailable; check local data validation')
            return
        self.send_response(200)
        self.send_header('Content-Type',content+'; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)


def main():
    parser=argparse.ArgumentParser(description='Local Healthcare Provider FP&A Copilot demo')
    parser.add_argument('--port',type=int,default=8501)
    args=parser.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Healthcare Provider FP&A Copilot: http://localhost:{args.port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
