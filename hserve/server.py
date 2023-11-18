import os
import socket
import signal
import sys


class HTTPError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"{status_code} {message}")

def handle_request(request):
    try:
        rows = request.split("\r\n")
        print(rows[0])
        method, path, _ = rows[0].split(" ")
        path = path.lstrip("/")
        is_directory = os.path.isdir(path)

        if path == "" or is_directory:
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
                response = f"HTTP/1.1 200 OK\r\nContent-Length: {len(content)}\r\n\r\n".encode() + content

        else:
            response_content = f"File or Directory not found".encode()
            response = f"HTTP/1.1 404 Not Found\r\nContent-Length: {len(response_content)}\r\n\r\n".encode() + response_content
    

    except Exception as e:
        print(f"Error handling request: {e}")
        response = b"HTTP/1.1 500 Internal Server Error\r\n\r\n500 Internal Server Error"

    return response

def start_server():
    HOST = "localhost"
    PORT = 8080

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind((HOST, PORT))
    listener.listen(1)
    print(f"Listening  : http://{HOST}:{PORT}")


    def shutdown(signum, frame):
        print("Shutting down gracefully...")
        listener.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    try:
        while True:
            client_socket, _ = listener.accept()

            with client_socket:

                request = client_socket.recv(1024).decode("utf-8")

                rows = request.split("\r\n")
                print(rows[0])
                method, path, _ = rows[0].split(" ")

                if method != "GET":
                    raise HTTPError(405, "Method not allowed")
                
                response = handle_request(request)
                client_socket.sendall(response)
    except KeyboardInterrupt:

        shutdown(signal.SIGINT, None)
    finally:
        listener.close()

if __name__ == "__main__":
    os.chdir(os.getcwd())
    start_server()