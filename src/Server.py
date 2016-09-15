import socket
import json
import select
import sys
import queue
import src.message as message
import src.DbManager as Db
from Crypto.PublicKey import RSA

# General stuff to add:
# TODO: allow server to encrypt connections between client and server. # IMPLEMENT DIFFIE HELLMAN
# TODO: Implement a group chat system.

class Server:
    def __init__(self):
        super().__init__()
        self.running = False
        self.HOST = '127.0.0.1'
        self.PORT = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # debug
        self.users = {}  # String : Connection
        self.dbmgr = Db.DatabaseManager("enchat", "postgres", "develpass")
        self.load_config()

    def load_config(self):
        try:
            json_data = json.load(open("../server_config.json"))
            self.HOST = json_data["server-address"]
            self.PORT = json_data["port"]
            return True
        except FileNotFoundError:
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
        self.sock.listen(5)
        # Type : { Connection : Queue }
        message_queue = {}
        inputs = [self.sock, sys.stdin]
        outputs = []
        while self.running:
            try:
                inputs_ready, outputs_ready, _ = select.select(inputs, outputs, [])
                for connection in inputs_ready:
                    if connection is self.sock:  # TODO: break down into more functiions
                        # Handle initial client connections
                        conn, addr = connection.accept()
                        print("New connection from ", addr)
                        conn.setblocking(0)
                        inputs.append(conn)
                        # create a queue
                        message_queue[conn] = queue.Queue()
                    elif connection is sys.stdin:
                        # Handle server admin commands perhaps
                        # TODO: Handle admin input
                        print("! ADMIN INPUT NEEDS IMPLEMENTATION !")
                    else:
                        received = ""
                        received = connection.recv(1024).decode('utf-8')
                        if len(received) > 0:
                            self.handle_user_conn(message_queue, connection, received, outputs, inputs)

                for connection in outputs_ready:
                    try:
                        next_msg = message_queue[connection].get_nowait()
                    except queue.Empty:
                        outputs.remove(connection)
                    else:
                        connection.send(next_msg.encode('utf-8'))

            except select.error:
                print("Select threw an error!")

    def handle_user_conn(self, message_queue, connection, received, outputs, inputs):
        json_data = json.loads(received)
        # Handle unique connections via lookup with self.users
        if connection not in self.users.values():
            if json_data['type'] == message.REQUEST_TYPE:
                args = json_data['args']
                if json_data['request'] == message.AUTH_REQUEST:
                    print('Attempted login of {}'.format(args[0]), end=": ")
                    if self.dbmgr.validate_user(args[0], args[1]):  # if valid
                        if args[0] in self.users.keys():  # if user is already logged in
                            print("ALREADY LOGGED IN!")
                            self.queue_message(message_queue, message.Response(message.ERROR, "This user is already"
                                                                                              " logged in!").to_json()
                                               , connection, outputs)
                        else:
                            print("SUCCESS")
                            self.queue_message(message_queue, message.Response(message.SUCCESS,
                                                                               "Authentication successful "
                                                                               "with name {}.".format(args[0])
                                                                               ).to_json(), connection, outputs)
                            self.users[args[0]] = connection
                            print(self.users)
                    else:
                        print("FAILED")
                        self.queue_message(message_queue, message.Response(message.ERROR,
                                                                           "Authentication unsuccessful!: "
                                                                           "Invalid username or password")
                                           .to_json(), connection, outputs)
                elif json_data['request'] == message.REGISTER_REQUEST:
                    if not self.dbmgr.user_exists(args[0]):
                        #  register
                        if self.dbmgr.add_user(args[0], args[1]):
                            self.queue_message(message_queue, message.Response(message.SUCCESS,
                                                                               "Authentication successful as: {}"
                                                                               .format(args[0])).to_json(),
                                               connection, outputs)
                            print("New user registered as {}!".format(args[0]))
                            self.users[args[0]] = connection
                            if connection not in outputs:
                                outputs.append(connection)
                    else:
                        self.queue_message(message_queue, message.Response(message.ERROR,
                                                            "Name Taken! Try another")
                                                          .to_json(), connection, outputs)

            else:
                # hasn't logged in # need to handle /register
                resp = message.Response(message.ERROR, "Please connect via a valid username/password "
                                                       "or register using /register <username> "
                                                       "<password>").to_json()
                self.queue_message(message_queue, resp, connection, outputs)
        else:  # connected user
            if json_data['type'] in [message.SECUREMESSAGE_TYPE, message.MESSAGE_TYPE]:
                existing_user = False
                outgoing_conn = None
                for username, user_conn in self.users.items():
                    if username == json_data['to']:
                        existing_user = True
                        outgoing_conn = user_conn
                        break
                if not existing_user:  # if user isn't connected
                    response = message.Response(message.ERROR, "User not connected!").to_json()
                    self.queue_message(message_queue, response, outgoing_conn, outputs)
                else:
                    self.queue_message(message_queue, json.dumps(json_data), outgoing_conn, outputs)
                print(json_data['from'], " -> ", json_data['to']
                      , " : SECURE" if json_data['type'] == message.SECUREMESSAGE_TYPE else "")
            elif json_data['type'] == 'logout':
                inputs.remove(connection)
                try:
                    outputs.remove(connection)
                except ValueError:
                    pass
                del self.users[[k for k, v in self.users.items() if v == connection][0]]

    def queue_message(self, message_queue, msg, connection, outputs):
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
