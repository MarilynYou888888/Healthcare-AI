"""Local-only demo server. Serves explicit assets and read-only financial views."""
import argparse
import json
import ipaddress
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from provider_fpa.benchmark import load_company
from provider_fpa.scenario import load_baseline
from provider_fpa.investigation import investigation_catalog, investigation_view, review_investigation

WEB = Path(__file__).resolve().parents[1] / 'web'
ASSETS = {'/presentation.js':('presentation.js','text/javascript'),'/charts.js':('charts.js','text/javascript'),'/benchmark-view.js':('benchmark-view.js','text/javascript'),'/investigation.js':('investigation.js','text/javascript'),'/executive.js':('executive.js','text/javascript'),'/interpretation.js':('interpretation.js','text/javascript'),'/scenario-view.js':('scenario-view.js','text/javascript'),'/scenario.js':('scenario.js','text/javascript'),'/vendor/decimal.mjs':('vendor/decimal.mjs','text/javascript'),'/':('index.html','text/html'),'/app.js':('app.js','text/javascript'),'/style.css':('style.css','text/css')}

# Ticket 1: static, locally bundled import workspace. No upload endpoint.
ASSETS.update({
    '/import': ('import.html', 'text/html'),
    '/user-analysis.html': ('user-analysis.html', 'text/html'),
    **{'/' + name: (name, 'text/javascript') for name in (
        'commentary.js', 'payer-mix.js', 'user-investigation.js', 'user-workflows.js', 'import-view.js', 'import-schema.js', 'import-validation.js', 'import-worker.js',
        'vendor/xlsx.full.min.js', 'vendor/papaparse.min.js')},
    '/import.css': ('import.css', 'text/css'),
    '/sample-import.xlsx': ('sample-import.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
})



class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        try:
            if path == '/api/investigation/catalog':
                body, content = json.dumps(investigation_catalog()).encode(), 'application/json'
            elif path == '/api/investigation':
                query = parse_qs(urlsplit(self.path).query)
                view = investigation_view(query.get('case', ['C01'])[0], query.get('target', [None])[0],
                                          query.get('type', [None])[0], query.get('override', ['false'])[0] == 'true')
                body, content = json.dumps(view).encode(), 'application/json'
            elif path == '/api/baseline':
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
        self.respond(body, content)

    def do_POST(self):
        if urlsplit(self.path).path == '/api/user-investigation':
            self.user_investigation()
            return
        if urlsplit(self.path).path != '/api/investigation/review':
            self.send_error(501, 'Only session investigation review accepts POST')
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 16384:
                raise ValueError('Invalid review request size')
            request = json.loads(self.rfile.read(length))
            if not isinstance(request, dict) or set(request) != {'context', 'snapshot_id', 'decisions'}:
                raise ValueError('Invalid review request')
            result = review_investigation(**request)
        except (ValueError, TypeError, KeyError):
            self.respond(json.dumps({'error': 'Review rejected: reload the investigation and select an allowed action.'}).encode(),
                         'application/json', 400)
            return
        except OSError:
            self.respond(json.dumps({'error': 'Investigation data unavailable.'}).encode(), 'application/json', 503)
            return
        self.respond(json.dumps(result).encode(), 'application/json')

    def user_investigation(self):
        """Bounded same-origin loopback request; no request state is retained."""
        from provider_fpa.uploaded_investigation import uploaded_investigation
        try:
            host = self.headers.get('Host', '')
            parsed = urlsplit('http://' + host)
            if (not ipaddress.ip_address(self.client_address[0]).is_loopback
                    or parsed.hostname not in ('localhost', '127.0.0.1', '::1')
                    or parsed.port != self.server.server_port
                    or self.headers.get('Origin') != 'http://' + host
                    or self.headers.get_content_type() != 'application/json'):
                raise ValueError('Only same-origin loopback requests are accepted')
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 1024 * 1024:
                raise ValueError('Request limit exceeded')
            payload = json.loads(self.rfile.read(length))
            result = uploaded_investigation(payload)
        except (ValueError, TypeError, KeyError, AttributeError, ArithmeticError, RecursionError):
            self.respond(json.dumps({'error': 'Investigation request rejected. Check the selected records, units, confirmations and evidence settings; rerun before reviewing.'}).encode(), 'application/json', 400)
            return
        self.respond(json.dumps(result).encode(), 'application/json')

    def log_request(self, code='-', size='-'):
        # Never log the uploaded-analysis endpoint or user request/query content.
        if urlsplit(self.path).path == '/api/user-investigation':
            return
        super().log_request(code, size)

    def respond(self, body, content, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content + '; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
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
