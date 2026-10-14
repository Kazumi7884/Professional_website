"""Loopback-only preview with the site's real 404 document."""
import argparse
import gzip
from io import BytesIO
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Preview(SimpleHTTPRequestHandler):
    def send_head(self):
        accepted = []
        for item in self.headers.get('Accept-Encoding', '').split(','):
            parts = item.strip().split(';')
            if parts[0] != 'gzip':
                continue
            try:
                quality = next((float(p.strip()[2:]) for p in parts[1:] if p.strip().startswith('q=')), 1)
            except ValueError:
                quality = 0
            if quality > 0:
                accepted.append('gzip')
        path = Path(self.translate_path(self.path))
        if path.is_dir() and self.path.split('?', 1)[0].endswith('/'):
            path /= 'index.html'
        if accepted and path.is_file() and path.suffix in ('.html', '.css', '.js', '.json', '.xml', '.txt', '.svg'):
            body = gzip.compress(path.read_bytes(), mtime=0)
            self.send_response(200)
            self.send_header('Content-Type', self.guess_type(str(path)))
            self.send_header('Content-Encoding', 'gzip')
            self.send_header('Vary', 'Accept-Encoding')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Last-Modified', self.date_time_string(path.stat().st_mtime))
            self.end_headers()
            return BytesIO(body)
        return super().send_head()

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
    parser.add_argument('--directory', type=Path, default=ROOT / 'build')
    args = parser.parse_args()
    handler = partial(Preview, directory=str(args.directory.resolve()))
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
        print(f'Successor preview: http://127.0.0.1:{server.server_port}/', flush=True)
        server.serve_forever()
