import socket
import json
import select
import sys
import queue
import src.message as message
import src.DbManager as Db



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

    def start(self):
        self.running = True
        self.sock.bind((self.HOST, self.PORT))
        self.listen()

    def stop(self):
        self.running = False
        self.dbmgr.cur.close()
        self.dbmgr.conn.close()

    def listen(self):
        self.sock.listen(5)
        # Type : { Connection : Queue }
        message_queue = {}
        inputs = [self.sock, sys.stdin]
        outputs = []
        while self.running:
            try:
                inputs_ready, outputs_ready, _ = select.select(inputs, outputs, [])
                for connection in inputs_ready:
                    if connection is self.sock:
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
                if json_data['request'] == message.AUTH_REQUEST: # TODO: stop login override kicking users off
                    print('Attempted login of {}'.format(args[0]), end=": ")
                    if self.dbmgr.validate_user(args[0], args[1]):
                        print("SUCCESS")
                        message_queue[connection].put(message.Response(message.SUCCESS,
                                                                       "Authentication successful "
                                                                       "with name {}.".format(args[0])
                                                                       ).to_json())
                        self.users[args[0]] = connection
                        if connection not in outputs:
                            outputs.append(connection)
                    else:
                        print("FAILED")
                        message_queue[connection].put(message.Response(message.ERROR,
                                                                       "Authentication unsuccessful!: "
                                                                       "Invalid username or password")
                                                      .to_json())
                    if connection not in outputs:
                        outputs.append(connection)
                elif json_data['request'] == message.REGISTER_REQUEST:
                    if not self.dbmgr.user_exists(args[0]):
                        #  register
                        if self.dbmgr.add_user(args[0], args[1]):
                            message_queue[connection].put(message.Response(message.SUCCESS,
                                                                           "Authentication successful as: {}"
                                                                           .format(args[0])).to_json())
                            print("New user registered as {}!".format(args[0]))
                            self.users[args[0]] = connection
                            if connection not in outputs:
                                outputs.append(connection)
                    else:
                        message_queue[connection].put(message.Response(message.ERROR,
                                                                       "Name Taken! Try another")
                                                      .to_json())
                        if connection not in outputs:
                            outputs.append(connection)

            else:
                # hasn't logged in # need to handle /register
                resp = message.Response(message.ERROR, "Please connect via a valid username/password "
                                                       "or register using /register <username> "
                                                       "<password>").to_json()
                message_queue[connection].put(resp)
                if connection not in outputs:
                    outputs.append(connection)
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
                    message_queue[connection].put(response)
                    if connection not in outputs:
                        outputs.append(connection)
                else:
                    message_queue[outgoing_conn].put(json.dumps(json_data))
                    if outgoing_conn not in outputs:
                        outputs.append(outgoing_conn)
            elif json_data['type'] == 'logout':
                inputs.remove(connection)
                try:
                    outputs.remove(connection)
                except ValueError:
                    pass
                del self.users[[k for k, v in self.users.items() if v == connection][0]]


if __name__ == "__main__":
    s = Server()
    try:
        s.start()
    except KeyboardInterrupt:
        print("Server closed!")
    finally:
        s.stop()
