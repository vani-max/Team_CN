from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class BackendAHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/":
            response = {
                "backend": "A",
                "status": "running"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Backend", "A")
            self.send_header("Cache-Control", "max-age=60")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())

        elif self.path == "/api/status":
            response = {
                "backend": "A",
                "status": "ok"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Backend", "A")
            self.send_header("Cache-Control", "max-age=60")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()


server = HTTPServer(("0.0.0.0", 3001), BackendAHandler)

print("Backend A running on port 3001")

server.serve_forever()
