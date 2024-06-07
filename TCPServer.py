import socket


class TCPServer:
    host = None
    port = None
    server_socket = None

    def __init__(self, host, port):
        self.server_socket = socket.socket()
        self.host = host
        self.port = port
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
    
    def __del__(self):
        self.server_socket.close()
    
    def get_request(self):
        client_socket, _ = self.server_socket.accept()
        request = client_socket.recv(1024).decode("utf-8")
        return request, client_socket

    def send_response(self, client_socket:socket, response:str):
        client_socket.send(response.encode("utf-8"))
        client_socket.close()
        return

    def accept_connections(self):
        while True:
            client_socket, client_addr = self.server_socket.accept()
            print("Connect addr:{}".format(client_addr))

            request = client_socket.recv(1024).decode("utf-8")
            # TBD. Get message and do procedure
            print("Request:{}".format(request))
            
            response = "Response: ...TBD\n"
            client_socket.send(response.encode("utf-8"))
            client_socket.close()