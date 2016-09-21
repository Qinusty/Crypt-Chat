import socket
import json
import select
import sys
import queue
from src import message as message
from src import DbManager as Db
from src import Encryption as crypto
from Crypto.PublicKey import RSA


# General stuff to add:
# TODO: Implement a group chat system.
# TODO: Fix user crashing not removing them from users.


class Server:
    def __init__(self):
        super().__init__()
        self.running = False
        self.HOST = '127.0.0.1'  # default
        self.PORT = 5000  # default
        # default values, overwritten by load_config (specify in server_config.json)
        self.db_user = 'postgres' ' default'
        self.db_host = '127.0.0.1'
        self.db_password = ''
        self.db_name = 'postgres'

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # debug
        self.users = {}  # String : Connection
        self.load_config()
        self.dbmgr = Db.DatabaseManager(self.db_name, self.db_host, self.db_user, self.db_password)
        print('Successfully connected to the Database')
        print('Running server on {}:{}'.format(self.HOST, self.PORT))
        print("Generating secure key...")
        self.server_key = RSA.generate(4096)
        self.keys = {}  # Connection : publicKey

    def load_config(self):
        try:
            json_data = json.load(open("server_config.json"))
            self.HOST = json_data["server-address"]
            self.PORT = json_data["port"]
            self.db_host = json_data["db-host"]
            self.db_user = json_data["db-user"]
            self.db_password = json_data["db-password"]
            self.db_name = json_data["db-name"]
            return True
        except FileNotFoundError:
            print("Config file not found! (server_config.json)")
            return False
        except ValueError:
            return False

    def start(self):
        self.running = True
        self.sock.bind((self.HOST, self.PORT))
        self.listen()

    def stop(self):
        self.running = False
        self.dbmgr.cur.close()
        self.dbmgr.conn.close()

    def listen(self):  # TODO: get the server to notice disconnections.
        # Type : { Connection : Queue }
        self.sock.listen(5)
        message_queue = {}
        inputs = [self.sock, sys.stdin]
        outputs = []
        while self.running:
            try:
                inputs_ready, outputs_ready, _ = select.select(inputs, outputs, [])
                for connection in inputs_ready:
                    if connection is self.sock:  # TODO: break down into more functions
                        # Handle initial client connections
                        conn, addr = connection.accept()
                        print("New connection from ", addr)
                        conn.setblocking(0)
                        inputs.append(conn)
                        # create a queue
                        message_queue[conn] = queue.Queue()
                        pubkey = self.public_key()
                        msg = {'type': 'pubkey', 'key': pubkey}
                        conn.send(json.dumps(msg).encode('utf-8'))
                    elif connection is sys.stdin:
                        # Handle server admin commands perhaps
                        # TODO: Handle admin input
                        print("! ADMIN INPUT NEEDS IMPLEMENTATION !")
                    else:
                        received = connection.recv(4096)
                        if len(received) > 0:
                            received = received.decode('utf-8')
                            self.handle_user_conn(message_queue, connection, received, outputs, inputs)

                for connection in outputs_ready:
                    try:
                        next_msg = message_queue[connection].get_nowait()
                    except queue.Empty:
                        outputs.remove(connection)
                    else:

                        self.send_message(next_msg, connection)

            except select.error:
                print("Select threw an error!")

    def handle_user_conn(self, message_queue, connection, received, outputs, inputs):
        json_data = json.loads(received)
        # Handle unique connections via lookup with self.users

        if connection not in self.users.values():
            if json_data['type'] == 'pubkey':
                key = RSA.importKey(json_data['key'])
                self.keys[connection] = key
            elif json_data['type'] == message.REQUEST_TYPE:
                args = json_data['args']
                if json_data['request'] == message.AUTH_REQUEST:
                    print('Attempted login of {}'.format(args[0]), end=": ")
                    passhash = crypto.decrypt_message(args[1], self.server_key)
                    if self.dbmgr.validate_user(args[0], passhash):  # if valid
                        if args[0] in self.users.keys():  # if user is already logged in
                            print("ALREADY LOGGED IN!")
                            queue_message(message_queue, message.Response(message.ERROR, "This user is already"
                                                                                         " logged in!").to_json(),
                                          connection, outputs)
                        else:
                            print("SUCCESS")

                            queue_message(message_queue, message.Response(message.SUCCESS,
                                                                          "Authentication successful "
                                                                          "with name {}.".format(args[0])
                                                                          ).to_json(), connection, outputs)
                            self.users[args[0]] = connection
                    else:
                        print("FAILED")
                        queue_message(message_queue, message.Response(message.ERROR,
                                                                      "Authentication unsuccessful!: "
                                                                      "Invalid username or password")
                                      .to_json(), connection, outputs)
                elif json_data['request'] == message.REGISTER_REQUEST:
                    if not self.dbmgr.user_exists(args[0]):
                        #  register
                        passhash = crypto.decrypt_message(args[1], self.server_key)
                        if self.dbmgr.add_user(args[0], passhash):
                            queue_message(message_queue, message.Response(message.SUCCESS,
                                                                          "Authentication successful as: {}"
                                                                          .format(args[0])).to_json(),
                                          connection, outputs)
                            print("New user registered as {}!".format(args[0]))
                            self.users[args[0]] = connection
                    else:
                        queue_message(message_queue, message.Response(message.ERROR,
                                                                      "Name Taken! Try another")
                                      .to_json(), connection, outputs)
            else:
                # hasn't logged in # need to handle /register
                resp = message.Response(message.ERROR, "Please connect via a valid username/password "
                                                       "or register using /register <username> "
                                                       "<password>").to_json()
                queue_message(message_queue, resp, connection, outputs)
        else:  # connected user
            if json_data['type'] in [message.MESSAGE_TYPE]:
                existing_user = False
                outgoing_conn = None
                for username, user_conn in self.users.items():
                    if username == json_data['to']:
                        existing_user = True
                        outgoing_conn = user_conn
                        break
                if not existing_user:  # if user isn't connected
                    response = message.Response(message.ERROR, "User not connected!")
                    queue_message(message_queue, response, outgoing_conn, outputs)
                else:
                    queue_message(message_queue, json.dumps(json_data), outgoing_conn, outputs)
                print(json_data['from'], " -> ", json_data['to'],
                      " : SECURE" if json_data['type'] == message.SECUREMESSAGE_TYPE else "")
            elif json_data['type'] == 'logout':
                inputs.remove(connection)
                try:
                    outputs.remove(connection)
                except ValueError:
                    pass
                del self.users[[k for k, v in self.users.items() if v == connection][0]]
            elif json_data['type'] == message.REQUEST_TYPE:
                if json_data['request'] == 'pubkey':
                    user = json_data['args'][0]
                    print('received request for {}\'s public key'.format(user))
                    conn = self.users.get(user)
                    if conn is None:
                        queue_message(message_queue, message.Response('InvalidUserError', user).to_json(),
                                      connection, outputs)
                        print('public key is not on record')
                    else:
                        key = self.keys[conn]
                        print('Found public key, sending it.')
                        queue_message(message_queue, message.Response('pubkey',
                                                                      key.exportKey('PEM').decode('utf-8'),
                                                                      tag=user).to_json(),
                                      connection, outputs)

    def send_message(self, msg, connection):
        data = msg.encode('utf-8')
        connection.send(data)

    def public_key(self):
        pubkey = self.server_key.publickey()
        return pubkey.exportKey('PEM').decode('utf-8')


def queue_message(message_queue, msg, connection, outputs):
    message_queue[connection].put(msg)
    if connection not in outputs:
        outputs.append(connection)

if __name__ == "__main__":
    s = Server()
    try:
        s.start()
    except KeyboardInterrupt:
        print("Server closed!")
    finally:
        s.stop()
