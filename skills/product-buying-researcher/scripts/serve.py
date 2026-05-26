#!/usr/bin/env python3
"""Serve product research results on localhost.

Usage: python3 serve.py <path-to-data.json>

Reads the product data JSON file, injects it into the HTML template,
and serves the result on an available local port. Opens the browser
automatically.
"""

import http.server
import os
import signal
import socket
import sys
import webbrowser

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
TEMPLATE_PATH = os.path.join(SKILL_DIR, "assets", "template.html")
DEFAULT_PORT = 8432


def find_open_port(start=DEFAULT_PORT, tries=50):
    for port in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


def build_page(data_path):
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    with open(data_path, "r", encoding="utf-8") as f:
        data = f.read()
    return template.replace("__PRODUCT_DATA__", data)


class Handler(http.server.BaseHTTPRequestHandler):
    page_html = b""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(self.page_html)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(self.page_html)

    def log_message(self, format, *args):
        pass


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 serve.py <path-to-data.json>")
        sys.exit(1)

    data_path = os.path.abspath(sys.argv[1])
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found")
        sys.exit(1)

    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: template not found at {TEMPLATE_PATH}")
        sys.exit(1)

    html = build_page(data_path)
    Handler.page_html = html.encode("utf-8")

    port = find_open_port()
    server = http.server.HTTPServer(("127.0.0.1", port), Handler)

    url = f"http://localhost:{port}"
    print(f"\n  Product research results ready at: {url}\n")
    print("  Press Ctrl+C to stop the server.\n")

    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
