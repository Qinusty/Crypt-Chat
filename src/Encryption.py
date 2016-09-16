from Crypto.Cipher import PKCS1_OAEP


def encrypt_communication(msg, key):
    return PKCS1_OAEP.new(key).encrypt(msg)

def decrypt_communication(cmsg, key):
    msg = PKCS1_OAEP.new(key).decrypt(cmsg)
    if isinstance(msg, bytes):
        msg = msg.decode('utf-8')
    return msg
