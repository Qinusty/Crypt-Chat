from Crypto.Cipher import PKCS1_OAEP
import binascii


def encrypt_communication(msg, key):
    return PKCS1_OAEP.new(key).encrypt(msg)


def decrypt_communication(cmsg, key):
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
    cipher_text = encrypt_communication(text, key)
    return binascii.hexlify(cipher_text).decode('utf-8')


def decrypt_message(cipher_text, key):
    """
    Takes ciphertext in the form of Hex and returns plaintext
    :param cipher_text: cipher text in form of hex encoded as utf-8
    :param key: a Private key
    :return: plaintext
    """
    cipher_text = binascii.unhexlify(cipher_text)
    text = decrypt_communication(cipher_text, key)

    return text