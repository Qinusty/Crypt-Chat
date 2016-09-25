import Server
import Client
import threading
import time
from src import DbManager
import src.Encryption as crypto
from Crypto.PublicKey import RSA



def test_encryption():
    key = RSA.generate(4096)
    text = "I am testing the encryption functions."
    cipher_text = crypto.encrypt_message(text, key.publickey())
    assert(text == crypto.decrypt_message(cipher_text, key))
    cipher_text = crypto.encrypt_message(text.encode('utf-8'), key.publickey())
    assert (text == crypto.decrypt_message(cipher_text, key))


def test_database():
    DbManager.DatabaseManager("postgres", "127.0.0.1", "postgres", "")

