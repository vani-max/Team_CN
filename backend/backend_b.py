from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class BackendBHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == "/":
            response = {
                "backend": "B",
                "status": "running"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Backend", "B")
            self.send_header("Cache-Control", "max-age=60")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())

        elif self.path == "/api/status":
            response = {
                "backend": "B",
                "status": "ok"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("X-Backend", "B")
            self.send_header("Cache-Control", "max-age=60")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()


server = HTTPServer(("0.0.0.0", 3002), BackendBHandler)

print("Backend B running on port 3002")

server.serve_forever()