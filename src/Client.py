import json
import socket
import select
import sys


class Client():
    def __init__(self):
        self.sock = socket.socket()
        self.client_name = ''
        self.server_port = 5000
        self.server_address = ''
        self.running = False

    def start(self):
        self.running = True
        connected = False
        self.server_address = input("Enter Server IP: ")
        self.sock.connect((self.server_address, self.server_port))
        self.client_name = input("Enter Name: ")
        while not connected:
            #try

            self.sock.send(self.client_name.encode('utf-8'))

            response = self.sock.recv(1024).decode('utf-8')

            json_data = json.loads(response)
            print(json_data['message'])
            if json_data['type'] == 'success':
                connected = True
            else:
                self.client_name = input("Enter Name: ")
        self.run()

    def run(self):
        inputs = [self.sock, sys.stdin]
        while self.running:
            inputready,_,_ = select.select(inputs,[],[])

            for s in inputready:
                if s == sys.stdin:
                    user_input = sys.stdin.readline()
                    if user_input.startswith('/'):
                        if user_input.lower().startswith('/msg'):
                            split_user_input = user_input.split(' ')
                            to = split_user_input[1]
                            text = " ".join(split_user_input[2:])
                            message = {'type': 'message', 'to': to, 'message': text}
                            json_message = json.dumps(message)
                            self.sock.send(json_message.encode('utf-8'))
                        elif user_input.lower() == '/exit\n':
                            self.stop()
                            sys.exit(0)

                if s == self.sock:
                    received = s.recv(1024).decode('utf-8')
                    json_data = json.loads(received)
                    if json_data['type'] == 'message':
                        print("From {}: {}".format(json_data['from'], json_data['message']))
                    elif json_data['type'] == 'error':
                        print("ERROR: " + json_data['message'])




    def stop(self):
        self.running = False
        self.sock.close()
        sys.exit(0)






if __name__ == "__main__":
    c = Client()
    c.start()