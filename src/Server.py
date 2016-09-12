import socket
import json
import select
import sys
import queue
import src.message as message

class User:
    def __init__(self, name, passhash):
        self.name = name
        self.passhash = passhash

class Server:
    def __init__(self):
        super().__init__()
        self.running = False
        self.HOST = '127.0.0.1'
        self.PORT = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # debug
        self.users = {}  # User : Connection

    def start(self):
        self.running = True
        self.sock.bind((self.HOST, self.PORT))
        self.listen()

    def stop(self):
        self.running = False

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
                        print("! ADMIN INPUT NEEDS IMPLEMENTATION !")
                    else:
                        received = ""
                        while len(received) == 0:
                            received = connection.recv(1024).decode('utf-8')
                        json_data = json.loads(received)
                        # Handle unique connections via lookup with self.users
                        if connection not in self.users.values():
                            if json_data['type'] == message.REQUEST_TYPE:
                                args = json_data['args']
                                if json_data['request'] == message.AUTH_REQUEST:
                                    # TODO: Implement database or filestore for users
                                    print("NOT IMPLEMENTED")
                                    message_queue[connection].put(message.Response(message.ERROR,
                                                                                   "Authentication not implemented, "
                                                                                   "register a new username"))
                                    if connection not in outputs:
                                        outputs.append(connection)
                                elif json_data['request'] == message.REGISTER_REQUEST:
                                    if args[0] not in self.users.keys(): # name not taken
                                        newuser = User(args[0], args[1])
                                        self.users[newuser] = connection # add user to self.users with connection
                                        message_queue[connection].put(message.Response('auth-success',
                                                                                       "Authentication successful as: {}"
                                                                                       .format(args[0])).to_json())
                                        print("New user registered as {}!".format(newuser.name))
                                        if connection not in outputs:
                                            outputs.append(connection)
                                    else: # name taken
                                        message_queue[connection].put(message.Response(message.ERROR,
                                                                                       "Name Taken! Try another"))
                                        if connection not in outputs:
                                            outputs.append(connection)

                            else:
                                # hasn't logged in # need to handle /register
                                resp = message.Response("auth-error", "Please connect via a valid username/password "
                                                                      "or register using /register <username> "
                                                                      "<password>").to_json()
                                message_queue[connection].put(resp)
                                if connection not in outputs:
                                    outputs.append(connection)
                        else:  # valid user account
                            if json_data['type'] in [message.SECUREMESSAGE_TYPE, message.MESSAGE_TYPE]:
                                existing_user = False
                                outgoing_conn = None
                                for user, user_conn in self.users.items():  # check if user exists #FIX how to iterate dict
                                    if user.name == json_data['to']:
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

                for connection in outputs_ready:
                    try:
                        next_msg = message_queue[connection].get_nowait()
                    except queue.Empty:
                        outputs.remove(connection)
                    else:
                        connection.send(next_msg.encode('utf-8'))

            except select.error:
                print("Select threw an error!")

if __name__ == "__main__":
    s = Server()
    try:
        s.start()
    finally:
        s.stop()
