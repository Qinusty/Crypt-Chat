import socket
import threading
from Crypto.Cipher import AES
import json
import select


class ConnectionThread(threading.Thread):
    def __init__(self, name, conn, addr):
        super().__init__()
        self.connection = conn
        self.connection.settimeout(None)
        self.client_address = addr
        self.client_name = name
        self.__running = False

    def run(self):
        disconnected = False
        while self.__running and not disconnected:
            try:
                received = ''
                while len(received) == 0:
                    received = self.connection.recv(1024).decode('utf-8')
                json_data = json.loads(received)
                print("data received from {0} at {1} going to {2}".format(self.client_name, self.client_address, json_data['to']))
                print("It says: ", json_data['message'])
                if s.connection_threads.get(json_data['to']) is None:
                    response = {'type': 'error', 'message': 'No user connected with this name!'}
                    self.connection.send(json.dumps(response).encode('utf-8'))
                else:
                    response = json_data
                    response['from'] = self.client_name
                    s.connection_threads[response['to']].connection.send(json.dumps(response).encode('utf-8'))
            except BrokenPipeError:
                print("Client at {0} has disconnected".format(self.client_address))
                disconnected = True
                self.stop()

    def start(self):
        self.__running = True
        return super().start()

    def stop(self):
        self.__running = False


class Server:
    def __init__(self):
        super().__init__()
        self.running = False
        self.HOST = '127.0.0.1'
        self.PORT = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # debug
        self.connection_threads = {}

    def start(self):
        self.running = True
        self.sock.bind((self.HOST, self.PORT))
        self.listen()

    def stop(self):
        self.running = False

    def listen(self):
        self.sock.listen(5)

        while self.running:
            conn, addr = self.sock.accept()
            conn.settimeout(5)
            name_assigned = False
            while not name_assigned:
                try:
                    name = conn.recv(1024).decode('utf-8')
                    if self.connection_threads.get(name) is None:
                        response = {'type': 'success', 'message': 'Name Granted! You are known as {}.'.format(name)}
                        name_assigned = True
                        conn.send(json.dumps(response).encode('utf-8'))
                        print("Connection from: {0}@{1}".format(name, addr))
                        thread = ConnectionThread(name, conn, addr)
                        self.connection_threads[name] = thread
                        thread.start()
                    else:
                        response = {'type': 'error', 'message': 'Name Already Taken!'}
                        conn.send(json.dumps(response).encode('utf-8'))
                except socket.timeout:
                    conn.close()
                    print("No name request from {0}, connection closed.".format(addr))


if __name__ == "__main__":
    s = Server()
    try:
        s.start()
    finally:
        s.stop()
