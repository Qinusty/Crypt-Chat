import psycopg2
import sys

class DatabaseManager:

    def __init__(self, dbname, host, user, password):
        self.conn = psycopg2.connect(database=dbname, user=user, password=password, host=host)
        self.cur = self.conn.cursor()
        self.conn.autocommit = True

    def validate_user(self, usn, passhash):
        try:
            self.cur.execute('SELECT passhash FROM users WHERE name = %s', (usn,))
        except psycopg2.ProgrammingError:
            print('Invalid database configuraton!')
            sys.exit(1)
        data = self.cur.fetchone()
        if data is not None and data[0] == passhash:
            return True
        else:
            return False

    def add_user(self, usn, passhash):
        try:
            self.cur.execute("INSERT INTO users (name, passhash) VALUES (%s, %s)", (usn, passhash))
        except psycopg2.IntegrityError:
            return False
        else:
            return True

    def user_exists(self, usn):
        self.cur.execute("SELECT id FROM users WHERE name = %s", (usn,))
        if self.cur.fetchone() is None:
            return False
        else:
            return True
