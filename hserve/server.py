import os
import socket
import signal
import sys


class HTTPError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"{status_code} {message}")


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
                
                response = f"HTTP/1.1 {200} OK\r\nContent-Type: text/html\r\n\r\n You are trying to access: {path}"
                client_socket.sendall(response.encode("utf-8"))
    except KeyboardInterrupt:

        shutdown(signal.SIGINT, None)
    finally:
        listener.close()

if __name__ == "__main__":
    start_server()