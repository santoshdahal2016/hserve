import os
import socket
import signal
import sys
import json


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler




fetch_reload_string = b"""
<script>
    // Function to fetch and reload every 1 second
    function fetchAndReload() {
        fetch('/_reload')
            .then(response => response.json())
            .then(data => {
                if (data.reload === 'true') {
                    console.log('Reloading page...');
                    location.reload(true); // Pass true to force a reload from the server
                }
            })
            .catch(error => console.error('Error fetching _reload:', error));
    }

    // Call the function every 1 second
    setInterval(fetchAndReload, 1000);
</script>
"""

FILE_CHANGED  = False

class FileChangedHandler(FileSystemEventHandler):

    def on_any_event(self, event):
        print("File Changed ")
        global FILE_CHANGED
        FILE_CHANGED = True

handler = FileChangedHandler()


observer = Observer()
observer.schedule(handler, path='.', recursive=True)
observer.start()



class HTTPError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"{status_code} {message}")



def handle_request(request):
    global FILE_CHANGED
    try:
        rows = request.split("\r\n")
        method, path, _ = rows[0].split(" ")
        path = path.lstrip("/")
        is_directory = os.path.isdir(path)

        if path == "_reload":
            # Return JSON response for "_reload" path
            json_response = json.dumps({"reload": "true" if FILE_CHANGED else "false"})
            FILE_CHANGED = False
            response = f"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: {len(json_response)}\r\n\r\n".encode() + json_response.encode()
            return response

        elif path == "" or is_directory:
            if is_directory:
                if os.path.exists(f"{path}/index.html"):
                    path = f"{path}/index.html"
                else: 
                    file_list = os.listdir(path)
                    links = "\n".join(f'<a href="/{file}">{file}</a> <br>' for file in file_list)
                    content = f"<html><body>{links}</body></html>".encode()
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(content)}\r\n\r\n".encode() + content
                    return response
            else:
                if os.path.exists(f"index.html"):
                    path = f"index.html"
                else: 
                    current_directory = os.getcwd()
                    file_list = os.listdir(current_directory)
                    links = "\n".join(f'<a href="/{file}">{file}</a> <br>' for file in file_list)
                    content = f"<html><body>{links}</body></html>".encode()
                    response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(content)}\r\n\r\n".encode() + content
                    return response       
        
        if os.path.exists(path):
            with open(f"{path}", "rb") as file:
                content = file.read()
                content +=  fetch_reload_string

                response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(content)}\r\n\r\n".encode() + content

        else:
            response_content = f"File or Directory not found".encode()
            response = f"HTTP/1.1 404 Not Found\r\nContent-Length: {len(response_content)}\r\n\r\n".encode() + response_content
    

    except Exception as e:
        print(f"Error handling request: {e}")
        response = b"HTTP/1.1 500 Internal Server Error\r\n\r\n500 Internal Server Error"

    return response


def serve_http(port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", port))
    server_socket.listen(1)
    print(f"HTTP server listening on port {port}")

    while True:
        client_socket, _ = server_socket.accept()

        with client_socket:

            request = client_socket.recv(1024).decode("utf-8")

            rows = request.split("\r\n")
            print(rows[0])
            method, path, _ = rows[0].split(" ")

            if method != "GET":
                raise HTTPError(405, "Method not allowed")
            
            response = handle_request(request)
            client_socket.sendall(response)


def start_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 8080))
    server_socket.listen(1)
    print(f"HTTP server listening on port {8080}")


    def shutdown(signum, frame):
        print("Shutting down gracefully...")
        server_socket.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)


    try:
        while True:
            client_socket, _ = server_socket.accept()

            with client_socket:

                request = client_socket.recv(1024).decode("utf-8")

                rows = request.split("\r\n")
                method, path, _ = rows[0].split(" ")

                if method != "GET":
                    raise HTTPError(405, "Method not allowed")
                
                response = handle_request(request)
                client_socket.sendall(response)
    except KeyboardInterrupt:
 
        shutdown(signal.SIGINT, None)
    finally:
        observer.stop()
        observer.join()
        server_socket.close()



if __name__ == "__main__":
    os.chdir(os.getcwd())
    start_server()