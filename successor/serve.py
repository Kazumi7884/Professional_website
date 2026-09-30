"""Loopback-only preview with the site's real 404 document."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Preview(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        self.send_error(404)

    def send_error(self, code, message=None, explain=None):
        error_page = Path(self.directory) / '404.html'
        if code == 404 and error_page.is_file():
            body = error_page.read_bytes()
            self.send_response(404)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            if self.command != 'HEAD':
                self.wfile.write(body)
        else:
            super().send_error(code, message, explain)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    handler = partial(Preview, directory=str(ROOT / 'build'))
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
        print(f'Successor preview: http://127.0.0.1:{server.server_port}/', flush=True)
        server.serve_forever()
