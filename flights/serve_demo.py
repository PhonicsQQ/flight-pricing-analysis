"""Serve only the generated demo, bound to loopback; never expose the project root."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from flights.freeze import ROOT


def main():
    directory = ROOT/'artifacts/demo'
    if not (directory/'data.json').exists():
        raise SystemExit('First run: python3 -m flights.export_demo')
    handler = partial(SimpleHTTPRequestHandler, directory=str(directory))
    with ThreadingHTTPServer(('127.0.0.1',4174),handler) as server:
        print('Flight Notes local demo: http://127.0.0.1:4174',flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
