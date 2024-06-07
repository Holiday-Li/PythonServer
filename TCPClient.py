import socket

class TCPClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self._connect()

    def _connect(self):
        self.client = socket.socket()
        self.client.connect((self.host, self.port))

    def send(self, message:str):
        self.client.send(message.encode("utf-8"))
    
    def recv(self, buffer_size=1024):
        return self.client.recv(buffer_size).decode("utf-8")
    
    def close(self):
        self.client.close()