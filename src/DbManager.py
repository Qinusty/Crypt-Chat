import psycopg2


class DatabaseManager:

    def __init__(self, dbname, user, password):
        self.conn = psycopg2.connect(database=dbname, user=user, password=password)
        self.cur = self.conn.cursor()
        self.conn.autocommit = True

    def validate_user(self, usn, passhash):
        self.cur.execute('SELECT passhash FROM users WHERE name = %s', (usn))
        data = self.cur.fetchone()
        if data[0] == passhash:
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
