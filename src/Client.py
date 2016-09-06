import json
import socket
import select
import sys
from Crypto.Cipher import AES
from Crypto import Random
import hashlib
import binascii



class Client:
    def __init__(self):
        self.passwords = {}
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
            inputready, _, _ = select.select(inputs, [], [])

            for s in inputready:
                if s == sys.stdin:
                    user_input = sys.stdin.readline()
                    if user_input.startswith('/'):
                        if user_input.lower().startswith('/msg'):
                            split_user_input = user_input.split(' ')
                            to = split_user_input[1]
                            text = " ".join(split_user_input[2:])
                            if self.passwords.get(to) is not None:
                                cipher_text, iv = encrypt_message(text, self.passwords[to])
                                message = {'type': 'secure-message', 'to': to, 'iv': iv, 'message': cipher_text}
                            else:
                                message = {'type': 'message', 'to': to, 'message': text}
                            json_message = json.dumps(message)
                            self.sock.send(json_message.encode('utf-8'))
                        elif user_input.lower().startswith('/password'):  # /password John P4$$w0rd
                            split_user_input = user_input.strip().split(' ')
                            # add a new password
                            self.passwords[split_user_input[1]] = split_user_input[2].encode()
                            print("Password added! Try sending this person a message!")
                        elif user_input.lower() == '/exit\n':
                            self.stop()
                            sys.exit(0)

                if s == self.sock:
                    received = s.recv(1024).decode('utf-8')
                    json_data = json.loads(received)
                    if json_data['type'] == 'message':
                        print("From {}: {}".format(json_data['from'],
                                                   json_data['message']))
                    elif json_data['type'] == 'secure-message':
                        if self.passwords.get(json_data['from']) is None:
                            print("You received a message from {} but you don't have a password set for encryption "
                                  "with them.\nThe key must be synchronous and shared between the two of you.\n"
                                  "You can enter one now by using the /password <NAME> <Password> command."
                                  .format(json_data['from']))
                        else:
                            print("Secure Message From {}: \n{}".format(json_data['from'],
                                                                       decrypt_message(json_data['message'],
                                                                       self.passwords[json_data['from']],
                                                                       json_data['iv'])))

                    elif json_data['type'] == 'error':
                        print("ERROR: " + json_data['message'])

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
    text = text.encode('utf-8') # encode utf-8
    cipher_text = enc.encrypt(text)
    #print(len(cipher_text)) # dedbug
    ## padd for decoding
    return binascii.hexlify(cipher_text).decode('utf-8'), binascii.hexlify(iv).decode('utf-8')


def decrypt_message(cipher_text, password, iv):
    cipher_text = binascii.unhexlify(cipher_text.encode('utf-8'))
    iv = binascii.unhexlify(iv.encode('utf-8'))
    key = hashlib.sha256(password).digest()
    dec = AES.new(key, AES.MODE_CBC, iv)

    return dec.decrypt(cipher_text).decode().strip()

## utf-8 encode -> encrypt -> b64 encode -> send -> b64 decode -> decrypt -> utf-8 decode


if __name__ == "__main__":
    c = Client()
    c.start()

