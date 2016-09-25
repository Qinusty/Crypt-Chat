import json

SUCCESS = 'success'
ERROR = 'error'

MESSAGE_TYPE = 'message'
SECUREMESSAGE_TYPE = 'secure-message'
REQUEST_TYPE = 'request'

AUTH_REQUEST = 'auth'
REGISTER_REQUEST = 'register'
KEY_REQUEST = 'key'


class Base:
    def __init__(self):
        self.data = {}

    def to_json(self):
        return json.dumps(self.data)


class Message(Base):
    def __init__(self, to, message, fr, group_flag=False):
        super().__init__()
        if not group_flag:
            self.data['type'] = MESSAGE_TYPE
        else:
            self.data['type'] = 'group-message'
        self.data['to'] = to
        self.data['message'] = message
        self.data['from'] = fr


class Request(Base):
    def __init__(self, request, args):
        super().__init__()
        self.data['type'] = REQUEST_TYPE
        self.data['request'] = request
        self.data['args'] = args


class Response(Base):
    def __init__(self, type, message='', tag=None, id=None):
        super().__init__()
        self.data['type'] = type
        self.data['message'] = message
        if tag is not None:
            self.data['tag'] = tag
        if id is not None:
            self.data['id'] = id

def parse(json_data):
    # return a message object
    if json_data['type'] == MESSAGE_TYPE:
        msg = Message(json_data['to'], json_data['message'], json_data.get('from'))
    elif json_data['type'] == REQUEST_TYPE:
        msg = Request(json_data['request'], json_data['args'])
    else:
        msg = Response(json_data['type'], json_data['message'])

    return msg
