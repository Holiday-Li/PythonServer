import socket

class UDPServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((self.host, self.port))

    def __del__(self):
        self.server.close()
    
    def get_request(self):
        data, client_addr = self.server.recvfrom(1024)
        data = data.decode("utf-8")
        return data, client_addr
    
    def send_response(self, client_addr, data):
        self.server.sendto(data.encode("utf-8"), client_addr)
        return

if __name__ == "__main__":
    host = socket.gethostname()
    port = 12345
    udp_server = UDPServer(host, port)
    while True:
        data, client_addr = udp_server.get_request()
        print("Recv:{} - from {}".format(data, client_addr))
        response_data = data.upper()
        print("Send:{} - to {}".format(response_data, client_addr))
        udp_server.send_reponse(client_addr, response_data)