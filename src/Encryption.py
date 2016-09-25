from Crypto.Cipher import PKCS1_OAEP
import binascii


def __encrypt(msg, key):
    return PKCS1_OAEP.new(key).encrypt(msg)


def __decrypt(cmsg, key):
    msg = PKCS1_OAEP.new(key).decrypt(cmsg)
    if isinstance(msg, bytes):
        msg = msg.decode('utf-8')
    return msg


def encrypt_message(text, key):
    """
    Takes Text and returns hex ciphertext ready for sending.
    :param text: Text to encrypt
    :param key: public key to encrypt with
    :return: ciphertext as hex
    """
    if not isinstance(text, bytes):
        text = text.encode('utf-8')
    cipher_text = __encrypt(text, key)
    return binascii.hexlify(cipher_text).decode('utf-8')


def decrypt_message(cipher_text, key):
    """
    Takes ciphertext in the form of Hex and returns plaintext
    :param cipher_text: cipher text in form of hex encoded as utf-8
    :param key: a Private key
    :return: plaintext
    """
    cipher_text = binascii.unhexlify(cipher_text)
    text = __decrypt(cipher_text, key)

    return text
