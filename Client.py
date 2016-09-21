import json
import socket
import select
import sys
import queue
from Crypto.Hash import SHA512
from Crypto.PublicKey import RSA
import binascii
from src import message as message
from src import Encryption as crypto

class Client:
    def __init__(self):
        self.sock = socket.socket()
        self.client_name = ''
        self.server_port = 5000
        self.server_address = ''
        self.running = False
        print("Generating secure key...")
        self.client_key = RSA.generate(4096)
        self.server_key = None
        self.user_keys = {}   # username : publicKey
        # TODO: Add logs to prepare for seperate channels of communication.
        self.group_logs = {}  # username : [String]
        self.user_logs = {}   # username : [String]

    def load_config(self):
        try:
            json_data = json.load(open("./config.json"))
            self.server_address = json_data["server-address"]
            self.server_port = json_data["port"]
            return True
        except FileNotFoundError:
            print("Config file not found!")
            return False
        except ValueError:
            return False

    def start(self):
        self.running = True
        connected = False
        if self.load_config():
            try:
                self.sock.connect((self.server_address, self.server_port))
                connected = True
                print("Connected to {}:{} via config".format(self.server_address, self.server_port))
            except:
                print("Config not valid!")
        while not connected:
            try:
                self.server_address = input("Enter Server IP: ")
                self.sock.connect((self.server_address, self.server_port))
                connected = True
                print("Successfully Connected to {}!".format(self.server_address))
            except ConnectionRefusedError:
                print("Invalid IP or server did not respond.")
        self.run()

    def run(self):
        waiting_for_key = []
        message_queue = queue.Queue()
        inputs = [self.sock, sys.stdin]
        while self.running:
            inputs_ready, _, _ = select.select(inputs, [], [])
            for s in inputs_ready:
                if s == sys.stdin:  # TODO: break down into functions
                    user_input = sys.stdin.readline()
                    if user_input.startswith('/'):
                        if user_input.lower().startswith('/msg'):
                            split_user_input = user_input.split(' ')
                            to = split_user_input[1]
                            text = " ".join(split_user_input[2:])
                            json_message = message.Message(to, text, self.client_name).data
                            message_queue.put(json_message)
                        elif user_input.lower().startswith('/register'):
                            split_user_input = user_input.strip().split(' ')
                            usn = split_user_input[1]
                            self.client_name = usn
                            pswhash = hash_password(split_user_input[2])
                            pswhash = crypto.encrypt_message(pswhash, self.server_key)
                            request = message.Request(message.REGISTER_REQUEST, [usn, pswhash]).data
                            message_queue.put(request)

                        elif user_input.lower().startswith('/login'):
                            split_user_input = user_input.strip().split(' ')
                            try:
                                usn, psw = split_user_input[1:]
                            except ValueError:
                                print("Invalid command! /login <username> <password>")
                            passhash = hash_password(psw)
                            passhash = crypto.encrypt_message(passhash, self.server_key)
                            rq = message.Request(message.AUTH_REQUEST, [usn, passhash])
                            self.client_name = usn
                            #  print(rq.to_json())
                            message_queue.put(rq.data)
                        elif user_input.lower() == '/exit\n':
                            self.stop()
                            sys.exit(0)

                if s == self.sock:
                    received = s.recv(4096).decode('utf-8')
                    if len(received) > 0:
                        json_data = json.loads(received)
                        if json_data['type'] == 'pubkey':
                            if json_data.get('tag') is None:  # Server public key
                                print('Received Handshake request')
                                self.server_key = RSA.importKey(json_data['key'])
                                msg = {'type': 'pubkey', 'key':  self.client_key.publickey()
                                                                                .exportKey('PEM')
                                                                                .decode('utf-8')}
                                s.send(json.dumps(msg).encode('utf-8'))
                                print('Performing Handshake...')
                            else:
                                user = json_data['tag']
                                print('Server returned public key for {}.'.format(user))
                                self.user_keys[user] = RSA.importKey(json_data['message'])
                                for msg in waiting_for_key:
                                    if user == msg['to']:
                                        message_queue.put(msg)  # put back in message queue to be sent
                                        # print('Resending message: {} \nto {}.'.format(msg['message'], msg['to']))
                                        waiting_for_key.remove(msg)  # remove from waiting
                        elif json_data['type'] == 'message':
                            msg = crypto.decrypt_message(json_data['message'], self.client_key)
                            print('<{}>: {}'.format(json_data['from'], msg))
                        elif json_data['type'] == 'error':
                            print("ERROR: " + json_data['message'])
                        elif json_data['type'] == 'InvalidUserError':  # remove from waiting
                            print('Server doesn\'t have public key for user, sorry')
                            for msg in waiting_for_key:
                                if user == json_data['message']:
                                    waiting_for_key.remove(msg)
                        elif json_data['type'] == 'auth-error':
                            print(json_data['message'])
                            self.client_name = ''
                        elif json_data['type'] == message.SUCCESS:
                            print(json_data['message'])

            while not message_queue.empty():
                msg = message_queue.get_nowait()

                if msg['type'] == 'message':
                    if msg['to'] not in self.user_keys.keys():
                        waiting_for_key.append(msg)  # put it in the waiting pile
                        # send a request for public key
                        # print('Don\'t have the public key, sending a request for it.')
                        msg = message.Request('pubkey', [msg['to'], ]).data
                    else:
                        msg['message'] = crypto.encrypt_message(msg['message'].encode('utf-8'), self.user_keys[msg['to']])
                if isinstance(msg, dict):
                    data = json.dumps(msg)
                else:
                    data = msg
                data = data.encode('utf-8')
                #print(json.dumps(msg))
                self.sock.send(data)

    def stop(self):
        try:
            data = {'type': 'logout'}
            data = json.dumps(data)
            self.sock.send(data.encode('utf-8'))
            self.running = False
            self.sock.close()
        except:
            pass

        sys.exit(0)


def hash_password(pwd):
    pswhash = SHA512.new(pwd.encode('utf-8')).digest()
    pswhash = binascii.hexlify(pswhash)
    return pswhash


if __name__ == "__main__":
    c = Client()
    try:
        c.start()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    finally:
        c.stop()
        print("Client Closed!")

