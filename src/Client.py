import json
import socket
import select
import sys
import queue
from Crypto.Cipher import AES
from Crypto.Hash import SHA512
from Crypto import Random
import hashlib
import binascii
import src.message as message


class Client:
    def __init__(self):
        #TODO: CHECK FOR CONFIG, TAKE IP and PORT
        self.passwords = {}
        self.sock = socket.socket()
        self.client_name = ''
        self.server_port = 5000
        self.server_address = ''
        self.running = False

    def start(self):
        self.running = True
        connected = False
        while not connected:
            try:
                self.server_address = input("Enter Server IP: ")
                self.sock.connect((self.server_address, self.server_port))
                connected = True
            except:
                print("Invalid IP or server did not respond.")
        self.run()

    def run(self): # TODO: implement message_queue with Client and remove sock.send
        inputs = [self.sock, sys.stdin]
        while self.running:
            inputs_ready, _, _ = select.select(inputs, [], [])

            for s in inputs_ready:
                if s == sys.stdin:
                    user_input = sys.stdin.readline()
                    if user_input.startswith('/'):
                        if user_input.lower().startswith('/msg'):
                            split_user_input = user_input.split(' ')
                            to = split_user_input[1]
                            text = " ".join(split_user_input[2:])
                            if self.passwords.get(to) is not None:
                                cipher_text, iv = encrypt_message(text, self.passwords[to])
                                json_message = message.SecureMessage(to, cipher_text, iv, fr=self.client_name).to_json()
                            else:
                                json_message = message.Message(to, text, fr=self.client_name).to_json()
                            self.sock.send(json_message.encode('utf-8'))

                        elif user_input.lower().startswith('/password'):  # /password John P4$$w0rd
                            split_user_input = user_input.strip().split(' ')
                            # add a new password
                            self.passwords[split_user_input[1]] = split_user_input[2].encode()
                            print("Password added! Try sending this person a message!")

                        elif user_input.lower().startswith('/register'):
                            split_user_input = user_input.strip().split(' ')
                            usn = split_user_input[1]
                            self.client_name = usn
                            pswhash = SHA512.new(split_user_input[2].encode('utf-8')).digest()
                            pswhash = binascii.hexlify(pswhash).decode('utf-8')
                            request = message.Request(message.REGISTER_REQUEST, [usn, pswhash]).to_json()
                            self.sock.send(request.encode('utf-8'))
                            print("register request: ", request)

                        elif user_input.lower().startswith('/login'):
                            print("Requires implementation!")

                        elif user_input.lower() == '/exit\n':
                            self.stop()
                            sys.exit(0)

                if s == self.sock:
                    received = s.recv(1024).decode('utf-8')
                    if len(received) > 0:
                        json_data = json.loads(received)
                        if json_data['type'] == 'message':
                            print("From {}: {}".format(json_data['from'],
                                                       json_data['message']))
                        elif json_data['type'] == 'secure-message':
                            if self.passwords.get(json_data['from']) is None:
                                print("You received a message from {} but you don't have a password set for encryption "
                                      "with them.\nThe key must be symmetric and shared between the two of you.\n"
                                      "You can enter one now by using the /password <NAME> <Password> command."
                                      .format(json_data['from']))
                            else:
                                print("Secure Message From {}: \n{}".format(json_data['from'],
                                                                            decrypt_message(json_data['message'],
                                                                            self.passwords[json_data['from']],
                                                                            json_data['iv'])))

                        elif json_data['type'] == 'error':
                            print("ERROR: " + json_data['message'])
                        elif json_data['type'] == 'auth-error':
                            print(json_data['message'])
                            self.client_name = ''
                        elif json_data['type'] == 'auth-success':
                            print(json_data['message'])

    def stop(self):
        self.running = False
        self.sock.close()
        sys.exit(0)


def encrypt_message(text, password):
    key = hashlib.sha256(password).digest()
    iv = Random.new().read(AES.block_size)
    enc = AES.new(key, AES.MODE_CBC, iv)
    if len(text) % 16 != 0:
        text += ' ' * (16 - len(text) % 16)
    text = text.encode('utf-8')
    cipher_text = enc.encrypt(text)
    return binascii.hexlify(cipher_text).decode('utf-8'), binascii.hexlify(iv).decode('utf-8')


def decrypt_message(cipher_text, password, iv):
    cipher_text = binascii.unhexlify(cipher_text.encode('utf-8'))
    iv = binascii.unhexlify(iv.encode('utf-8'))
    key = hashlib.sha256(password).digest()
    dec = AES.new(key, AES.MODE_CBC, iv)

    return dec.decrypt(cipher_text).decode().strip()


if __name__ == "__main__":
    c = Client()
    c.start()

