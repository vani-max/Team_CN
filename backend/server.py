import sys
import json
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BACKEND = sys.argv[1]
PORT = int(sys.argv[2])

class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        data = {
            "backend": BACKEND,
            "status": "ok",
            "message": f"Hello from Backend {BACKEND}"
        }

        body = json.dumps(data).encode()

        etag = f'"{hashlib.md5(body).hexdigest()}"'

        if self.path == "/api/status":
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Backend", BACKEND)
            self.send_header("Cache-Control", "max-age=60")
            self.send_header("ETag", etag)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path == "/":
            response = f"Backend {BACKEND} is running!"
            response = response.encode()

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.send_header("X-Backend", BACKEND)
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)

        else:
            self.send_response(404)
            self.end_headers()

server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)

print(f"Backend {BACKEND} running on port {PORT}")

server.serve_forever()
