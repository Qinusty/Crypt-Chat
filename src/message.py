import json

SUCCESS = 'success'
ERROR = 'error'

MESSAGE_TYPE = 'message'
SECUREMESSAGE_TYPE = 'secure-message'
REQUEST_TYPE = 'request'

AUTH_REQUEST = 'auth'
REGISTER_REQUEST = 'register'


class Base:
    def __init__(self):
        self.data = {}

    def to_json(self):
        return json.dumps(self.data)


class Message(Base):
    def __init__(self, to, message, fr=None):
        super().__init__()
        self.data['type'] = MESSAGE_TYPE
        self.data['to'] = to
        self.data['message'] = message
        if fr is not None:
            self.data['from'] = fr


class SecureMessage(Message):
    def __init__(self, to, cipher_text, iv, fr=None):
        super().__init__(to, cipher_text, fr)
        self.data['type'] = SECUREMESSAGE_TYPE
        self.data['iv'] = iv


class Request(Base):
    def __init__(self, request, args):
        super().__init__()
        self.data['type'] = REQUEST_TYPE
        self.data['request'] = request
        self.data['args'] = args


class Response(Base):
    def __init__(self, type, message=''):
        super().__init__()
        self.data['type'] = type
        self.data['message'] = message


def parse(json_data):
    # return a message object
    if json_data['type'] == MESSAGE_TYPE:
        msg = Message(json_data['to'], json_data['message'], json_data.get('from'))
    elif json_data['type'] == SECUREMESSAGE_TYPE:
        msg = SecureMessage(json_data['to'], json_data['message'], json_data['iv'], json_data.get('from'))
    elif json_data['type'] == REQUEST_TYPE:
        msg = Request(json_data['request'], json_data['args'])
    else:
        msg = Response(json_data['type'], json_data['message'])

    return msg
