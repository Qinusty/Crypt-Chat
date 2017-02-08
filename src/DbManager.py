import sys
import sqlite3

class DatabaseManager:

    def __init__(self, dbname):
        self.conn = conn = sqlite3.connect(dbname)

    def validate_user(self, usn, passhash):
        cur = self.conn.execute("""SELECT passhash FROM users WHERE name = "%s";""" % (usn,))
        data = cur.fetchone()
        if data is not None and data[0] == passhash:
            return True
        else:
            return False

    def add_user(self, usn, passhash):
        self.conn.execute("""INSERT INTO users (name, passhash) VALUES ("%s", "%s");""" % (usn, passhash))
        return True;

    def user_exists(self, usn):
        cur = self.conn.execute("""SELECT id FROM users WHERE name = "%s";""" % (usn,))
        if cur.fetchone() is None:
            return False
        else:
            return True
