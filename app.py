from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"Received request: {self.path}", flush=True)

        if self.path == "/health":
            body = b"OK"
        else:
            body = b"Hello from my DevOps CI/CD application!"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def log_message(self, format, *args):
        print(f"HTTP: {format % args}", flush=True)


server = ThreadingHTTPServer(("127.0.0.1", 5000), AppHandler)
print("Application running on http://127.0.0.1:5000", flush=True)
server.serve_forever()
