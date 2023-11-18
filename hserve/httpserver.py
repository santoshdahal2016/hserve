import http.server
import socketserver

PORT = 8000  # Choose a port for your server
STATIC_FOLDER = "static"  # Change this to the path of your static files folder

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()